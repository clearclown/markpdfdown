#!/bin/bash
# ============================================================
# MarkPDFDown Parallel Converter
# ============================================================
# Usage:
#   ./scripts/parallel_convert.sh input.pdf output.md [pages_per_job] [max_parallel]
#
# Examples:
#   ./scripts/parallel_convert.sh book.pdf book.md           # Auto-detect pages, 4 parallel jobs
#   ./scripts/parallel_convert.sh book.pdf book.md 25        # 25 pages per job
#   ./scripts/parallel_convert.sh book.pdf book.md 25 8      # 25 pages per job, 8 parallel
#
# Requirements:
#   - podman
#   - .env file with API credentials
#   - pdfinfo (poppler-utils) for page count detection
# ============================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INPUT_PDF="${1:-}"
OUTPUT_MD="${2:-}"
PAGES_PER_JOB="${3:-50}"
MAX_PARALLEL="${4:-4}"
IMAGE_NAME="${IMAGE_NAME:-docker.io/jorbenzhu/markpdfdown}"
ENV_FILE="${ENV_FILE:-.env}"

# Temporary directory for intermediate files
TEMP_DIR=""

# Cleanup function
cleanup() {
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        echo -e "${YELLOW}Cleaning up temporary files...${NC}"
        rm -rf "$TEMP_DIR"
    fi
}
trap cleanup EXIT

# Print usage
usage() {
    echo "Usage: $0 <input.pdf> <output.md> [pages_per_job] [max_parallel]"
    echo ""
    echo "Arguments:"
    echo "  input.pdf       Input PDF file"
    echo "  output.md       Output Markdown file"
    echo "  pages_per_job   Pages to process per parallel job (default: 50)"
    echo "  max_parallel    Maximum parallel jobs (default: 4)"
    echo ""
    echo "Environment variables:"
    echo "  IMAGE_NAME      Container image (default: docker.io/jorbenzhu/markpdfdown)"
    echo "  ENV_FILE        Environment file (default: .env)"
    echo ""
    echo "Examples:"
    echo "  $0 book.pdf book.md"
    echo "  $0 book.pdf book.md 25 8"
    exit 1
}

# Check dependencies
check_dependencies() {
    local missing=()

    if ! command -v podman &> /dev/null; then
        missing+=("podman")
    fi

    if ! command -v pdfinfo &> /dev/null; then
        echo -e "${YELLOW}Warning: pdfinfo not found. Install poppler-utils for auto page detection.${NC}"
        echo -e "${YELLOW}Will prompt for total pages instead.${NC}"
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        echo -e "${RED}Error: Missing dependencies: ${missing[*]}${NC}"
        echo "Please install them first."
        exit 1
    fi
}

# Get total pages in PDF
get_total_pages() {
    local pdf_file="$1"

    if command -v pdfinfo &> /dev/null; then
        pdfinfo "$pdf_file" 2>/dev/null | grep -i "^Pages:" | awk '{print $2}'
    else
        echo ""
    fi
}

# Process a single page range
process_range() {
    local pdf_file="$1"
    local start_page="$2"
    local end_page="$3"
    local output_file="$4"
    local job_num="$5"

    echo -e "${BLUE}[Job $job_num] Processing pages $start_page-$end_page...${NC}"

    if podman run -i --env-file "$ENV_FILE" "$IMAGE_NAME" "$start_page" "$end_page" < "$pdf_file" > "$output_file" 2>/dev/null; then
        echo -e "${GREEN}[Job $job_num] Completed pages $start_page-$end_page${NC}"
        return 0
    else
        echo -e "${RED}[Job $job_num] Failed pages $start_page-$end_page${NC}"
        return 1
    fi
}

# Main function
main() {
    # Validate arguments
    if [ -z "$INPUT_PDF" ] || [ -z "$OUTPUT_MD" ]; then
        usage
    fi

    if [ ! -f "$INPUT_PDF" ]; then
        echo -e "${RED}Error: Input file not found: $INPUT_PDF${NC}"
        exit 1
    fi

    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}Error: Environment file not found: $ENV_FILE${NC}"
        echo "Create it with: cp .env.sample .env"
        exit 1
    fi

    check_dependencies

    # Get total pages
    TOTAL_PAGES=$(get_total_pages "$INPUT_PDF")

    if [ -z "$TOTAL_PAGES" ]; then
        echo -n "Enter total number of pages: "
        read TOTAL_PAGES
    fi

    if [ -z "$TOTAL_PAGES" ] || [ "$TOTAL_PAGES" -lt 1 ]; then
        echo -e "${RED}Error: Invalid page count${NC}"
        exit 1
    fi

    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}MarkPDFDown Parallel Converter${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo -e "Input:          $INPUT_PDF"
    echo -e "Output:         $OUTPUT_MD"
    echo -e "Total pages:    $TOTAL_PAGES"
    echo -e "Pages per job:  $PAGES_PER_JOB"
    echo -e "Max parallel:   $MAX_PARALLEL"
    echo -e "${GREEN}============================================================${NC}"

    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    echo -e "${BLUE}Temporary directory: $TEMP_DIR${NC}"

    # Calculate job ranges
    declare -a JOBS=()
    local start=1
    local job_num=1

    while [ $start -le $TOTAL_PAGES ]; do
        local end=$((start + PAGES_PER_JOB - 1))
        if [ $end -gt $TOTAL_PAGES ]; then
            end=$TOTAL_PAGES
        fi
        JOBS+=("$start:$end:$job_num")
        start=$((end + 1))
        job_num=$((job_num + 1))
    done

    local total_jobs=${#JOBS[@]}
    echo -e "${BLUE}Total jobs: $total_jobs${NC}"
    echo ""

    # Process jobs in parallel
    local running=0
    local completed=0
    local failed=0
    declare -a PIDS=()
    declare -a JOB_INFO=()

    for job in "${JOBS[@]}"; do
        IFS=':' read -r start end num <<< "$job"
        local output_file="$TEMP_DIR/part_$(printf "%04d" $num).md"

        # Wait if we've reached max parallel
        while [ $running -ge $MAX_PARALLEL ]; do
            for i in "${!PIDS[@]}"; do
                if ! kill -0 "${PIDS[$i]}" 2>/dev/null; then
                    wait "${PIDS[$i]}" && completed=$((completed + 1)) || failed=$((failed + 1))
                    unset 'PIDS[$i]'
                    running=$((running - 1))
                fi
            done
            PIDS=("${PIDS[@]}")  # Re-index array
            sleep 0.5
        done

        # Start new job
        process_range "$INPUT_PDF" "$start" "$end" "$output_file" "$num" &
        PIDS+=($!)
        JOB_INFO+=("$num:$start:$end:$output_file")
        running=$((running + 1))

        # Small delay to avoid overwhelming the API
        sleep 1
    done

    # Wait for remaining jobs
    echo -e "${BLUE}Waiting for remaining jobs to complete...${NC}"
    for pid in "${PIDS[@]}"; do
        wait "$pid" && completed=$((completed + 1)) || failed=$((failed + 1))
    done

    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "Completed: $completed / $total_jobs"
    if [ $failed -gt 0 ]; then
        echo -e "${RED}Failed: $failed${NC}"
    fi
    echo -e "${GREEN}============================================================${NC}"

    # Combine results
    echo -e "${BLUE}Combining results...${NC}"
    > "$OUTPUT_MD"  # Clear output file

    for part_file in $(ls "$TEMP_DIR"/part_*.md 2>/dev/null | sort); do
        if [ -f "$part_file" ]; then
            cat "$part_file" >> "$OUTPUT_MD"
            echo "" >> "$OUTPUT_MD"
            echo "" >> "$OUTPUT_MD"
        fi
    done

    # Final stats
    local output_size=$(wc -c < "$OUTPUT_MD" 2>/dev/null || echo "0")
    local output_lines=$(wc -l < "$OUTPUT_MD" 2>/dev/null || echo "0")

    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}Conversion Complete!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo -e "Output file:    $OUTPUT_MD"
    echo -e "Output size:    $output_size bytes"
    echo -e "Output lines:   $output_lines"
    echo -e "${GREEN}============================================================${NC}"

    if [ $failed -gt 0 ]; then
        echo -e "${YELLOW}Warning: $failed jobs failed. Check output for missing sections.${NC}"
        exit 1
    fi
}

main "$@"
