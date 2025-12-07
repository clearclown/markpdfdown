<div align="center">

<h1>MarkPDFDown</h1>
<p align="center">English | <a href="./README_zh.md">中文</a> | <a href="./README_ja.md">日本語</a> | <a href="./README_ru.md">Русский</a> | <a href="./README_fa.md">فارسی</a> | <a href="./README_ar.md">العربية</a></p>

[![Size]][hub_url]
[![Pulls]][hub_url]
[![Tag]][tag_url]
[![License]][license_url]
<p>A powerful tool that leverages multimodal large language models to transcribe PDF files into Markdown format.</p>

![markpdfdown](https://raw.githubusercontent.com/markpdfdown/markpdfdown/refs/heads/master/tests/markpdfdown.png)

</div>

## Overview

MarkPDFDown is designed to simplify the process of converting PDF documents into clean, editable Markdown text. By utilizing advanced multimodal AI models, it can accurately extract text, preserve formatting, and handle complex document structures including tables, formulas, and diagrams.

## Features

- **PDF to Markdown Conversion**: Transform any PDF document into well-formatted Markdown
- **Image to Markdown Conversion**: Transform image into well-formatted Markdown
- **Multi-Provider Support**: Works with OpenAI, DeepSeek, Gemini, Claude, Qwen, OpenRouter, and more
- **Multimodal Understanding**: Leverages AI to comprehend document structure and content
- **Format Preservation**: Maintains headings, lists, tables, and other formatting elements
- **Large Document Support**: Process books and documents with 200+ pages
- **Container Ready**: Run with Docker or Podman
- **Customizable Model**: Configure the model to suit your needs

## Demo
![](https://raw.githubusercontent.com/markpdfdown/markpdfdown/refs/heads/master/tests/demo_02.png)

## Installation

### Using uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/MarkPDFdown/markpdfdown.git
cd markpdfdown

# Install dependencies and create virtual environment
uv sync

```

### Using conda

```bash
conda create -n markpdfdown python=3.9
conda activate markpdfdown

# Clone the repository
git clone https://github.com/MarkPDFdown/markpdfdown.git
cd markpdfdown

# Install dependencies
pip install -e .
```
## Quick Start with Podman

```bash
# 1. Copy and edit configuration
cp .env.sample .env
# Edit .env: set your API key (GEMINI_API_KEY recommended)

# 2. Run conversion
podman run -i --env-file .env docker.io/jorbenzhu/markpdfdown < input.pdf > output.md
```

## Usage

### Basic Usage with uv
```bash
# Set up your API credentials
cp .env.sample .env
# Edit .env with your API key

# PDF to Markdown
uv run python main.py < input.pdf > output.md

# Image to Markdown
uv run python main.py < input_image.png > output.md
```

### Page Range Extraction
```bash
# Convert specific pages (e.g., pages 10-50)
uv run python main.py 10 50 < book.pdf > chapter.md
```

## Supported AI Providers

This tool supports multiple LLM providers. Set `LLM_PROVIDER` environment variable to switch providers.

| Provider | Models | Vision Support | Native Support | Best For |
|----------|--------|----------------|----------------|----------|
| **OpenAI** | gpt-4o, gpt-4o-mini | ✅ | ✅ | General use |
| **DeepSeek** | deepseek-chat, DeepSeek-VL2 | ✅ | ✅ | Cost-effective |
| **Google Gemini** | Gemini 2.5/3 Pro/Flash | ✅ | ✅ | Very large documents |
| **Qwen** | Qwen3-VL (8B/30B/235B) | ✅ | via OpenAI-compat | Large documents (256K context) |
| **OpenRouter** | 400+ models | ✅ | via OpenAI-compat | Model flexibility |

### OpenAI (Default)
```bash
export LLM_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."
export OPENAI_DEFAULT_MODEL="gpt-4o"  # Optional, defaults to gpt-4o
```

### DeepSeek (Recommended for Cost)
```bash
export LLM_PROVIDER="deepseek"
export DEEPSEEK_API_KEY="your-deepseek-api-key"
# Or use OPENAI_API_KEY with explicit base URL:
# export OPENAI_API_KEY="your-deepseek-api-key"
# export OPENAI_API_BASE="https://api.deepseek.com/v1"
export OPENAI_DEFAULT_MODEL="deepseek-chat"
```

### Google Gemini (Native SDK)
```bash
# Install Gemini support
uv sync --extra gemini
# Or: pip install google-genai

export LLM_PROVIDER="gemini"
export GEMINI_API_KEY="your-gemini-api-key"
export GEMINI_MODEL="gemini-2.5-flash"  # Optional, defaults to gemini-2.5-flash
```

### Qwen (Alibaba Cloud)
```bash
export LLM_PROVIDER="openai"  # Uses OpenAI-compatible mode
export OPENAI_API_KEY="your-dashscope-api-key"
export OPENAI_API_BASE="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
export OPENAI_DEFAULT_MODEL="qwen-vl-max"
```

### OpenRouter (Unified API for 400+ Models)
```bash
export LLM_PROVIDER="openai"  # Uses OpenAI-compatible mode
export OPENAI_API_KEY="your-openrouter-api-key"
export OPENAI_API_BASE="https://openrouter.ai/api/v1"
export OPENAI_DEFAULT_MODEL="google/gemini-2.5-pro"  # or any vision model
```

## Container Usage

### Docker
```bash
# OpenAI
docker run -i \
  -e LLM_PROVIDER=openai \
  -e OPENAI_API_KEY=your-api-key \
  jorbenzhu/markpdfdown < input.pdf > output.md

# DeepSeek
docker run -i \
  -e LLM_PROVIDER=deepseek \
  -e DEEPSEEK_API_KEY=your-deepseek-key \
  jorbenzhu/markpdfdown < input.pdf > output.md

# Gemini
docker run -i \
  -e LLM_PROVIDER=gemini \
  -e GEMINI_API_KEY=your-gemini-key \
  jorbenzhu/markpdfdown < input.pdf > output.md
```

### Podman
```bash
# OpenAI
podman run -i \
  -e LLM_PROVIDER=openai \
  -e OPENAI_API_KEY=your-api-key \
  docker.io/jorbenzhu/markpdfdown < input.pdf > output.md

# DeepSeek
podman run -i \
  -e LLM_PROVIDER=deepseek \
  -e DEEPSEEK_API_KEY=your-deepseek-key \
  docker.io/jorbenzhu/markpdfdown < input.pdf > output.md

# Gemini
podman run -i \
  -e LLM_PROVIDER=gemini \
  -e GEMINI_API_KEY=your-gemini-key \
  docker.io/jorbenzhu/markpdfdown < input.pdf > output.md
```

### Building Container Locally
```bash
# Docker
docker build -t markpdfdown .

# Podman
podman build -t markpdfdown .
```

## Processing Large Documents (200+ Pages)

For processing books and large documents, use the parallel processing script.

### Parallel Processing with Podman (Recommended)

```bash
# 1. Setup
cp .env.sample .env
# Edit .env: set GEMINI_API_KEY (recommended for large docs)

# 2. Install pdfinfo for page detection (optional)
# Ubuntu/Debian: sudo apt install poppler-utils
# Fedora: sudo dnf install poppler-utils
# macOS: brew install poppler

# 3. Run parallel conversion
./scripts/parallel_convert.sh book.pdf output.md

# Custom settings: 25 pages per job, 8 parallel workers
./scripts/parallel_convert.sh book.pdf output.md 25 8
```

### Manual Parallel Processing

```bash
# Setup
cp .env.sample .env
# Edit .env with your API key

# Run parallel jobs with Podman
podman run -i --env-file .env docker.io/jorbenzhu/markpdfdown 1 50 < book.pdf > part1.md &
podman run -i --env-file .env docker.io/jorbenzhu/markpdfdown 51 100 < book.pdf > part2.md &
podman run -i --env-file .env docker.io/jorbenzhu/markpdfdown 101 150 < book.pdf > part3.md &
podman run -i --env-file .env docker.io/jorbenzhu/markpdfdown 151 200 < book.pdf > part4.md &
wait

# Combine results
cat part{1,2,3,4}.md > complete.md
```

### Recommended Models for Large Documents

| Model | Context | Best For | Cost |
|-------|---------|----------|------|
| **Gemini 2.5 Flash** | 1M tokens | Large books, cost-effective | Low |
| **Gemini 2.5 Pro** | 1M tokens | Complex layouts | Medium |
| **Qwen3-VL** | 256K tokens | Long documents | Low |
| **DeepSeek-VL2** | Large | High-volume processing | Very Low |

### Progress Monitoring

```bash
# View progress while converting
podman run -i --env-file .env docker.io/jorbenzhu/markpdfdown < book.pdf 2>&1 | tee output.md

# With parallel script (shows colored progress)
./scripts/parallel_convert.sh book.pdf output.md
```

> **Tip**: For 200+ page books, use `GEMINI_API_KEY` with `gemini-2.5-flash` and 4-8 parallel workers.

## Development Setup

### Code Quality Tools

This project uses `ruff` for linting and formatting, and `pre-commit` for automated code quality checks.

#### Install development dependencies

```bash
# If using uv
uv sync --group dev

# If using pip
pip install -e ".[dev]"
```

#### Set up pre-commit hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run pre-commit on all files (optional)
pre-commit run --all-files
```

#### Code formatting and linting

```bash
# Format code with ruff
ruff format

# Run linting checks
ruff check

# Fix auto-fixable issues
ruff check --fix
```

## Requirements
- Python 3.9+
- [uv](https://astral.sh/uv/) (recommended for package management) or conda/pip
- Dependencies specified in `pyproject.toml`
- API key from one of the supported providers:
  - [OpenAI](https://platform.openai.com/) (gpt-4o, gpt-4o-mini)
  - [DeepSeek](https://platform.deepseek.com/) (DeepSeek-VL2)
  - [Qwen/Alibaba Cloud](https://dashscope.aliyun.com/) (Qwen3-VL)
  - [OpenRouter](https://openrouter.ai/) (400+ models including Gemini, Claude)

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch ( `git checkout -b feature/amazing-feature` )
3. Set up the development environment:
   ```bash
   uv sync --group dev
   pre-commit install
   ```
4. Make your changes and ensure code quality:
   ```bash
   ruff format
   ruff check --fix
   pre-commit run --all-files
   ```
5. Commit your changes ( `git commit -m 'feat: Add some amazing feature'` )
6. Push to the branch ( `git push origin feature/amazing-feature` )
7. Open a Pull Request

Please ensure your code follows the project's coding standards by running the linting and formatting tools before submitting.

## License
This project is licensed under the Apache License 2.0. See the LICENSE file for details.

## Roadmap

- [x] Native Google Gemini API support
- [x] Multi-provider abstraction layer
- [ ] Native Anthropic Claude API support
- [ ] GUI progress indicator with real-time status
- [ ] Streaming output for real-time preview
- [ ] Resume interrupted conversions
- [ ] Cost estimation before processing

## Acknowledgments
- Thanks to the developers of the multimodal AI models that power this tool
- Inspired by the need for better PDF to Markdown conversion tools

## References
- [DeepSeek-VL2](https://github.com/deepseek-ai/DeepSeek-VL2) - DeepSeek Vision-Language Models
- [Qwen3-VL](https://github.com/QwenLM/Qwen3-VL) - Qwen Vision-Language Models
- [OpenRouter](https://openrouter.ai/docs/features/multimodal/overview) - Unified API for 400+ Models
- [Gemini API](https://ai.google.dev/gemini-api/docs/image-understanding) - Google Gemini Image Understanding
- [Claude Vision](https://docs.anthropic.com/claude/docs/vision) - Anthropic Claude Vision Capabilities

[hub_url]: https://hub.docker.com/r/jorbenzhu/markpdfdown/
[tag_url]: https://github.com/markpdfdown/markpdfdown/releases
[license_url]: https://github.com/markpdfdown/markpdfdown/blob/main/LICENSE

[Size]: https://img.shields.io/docker/image-size/jorbenzhu/markpdfdown/latest?color=066da5&label=size
[Pulls]: https://img.shields.io/docker/pulls/jorbenzhu/markpdfdown.svg?style=flat&label=pulls&logo=docker
[Tag]: https://img.shields.io/github/release/markpdfdown/markpdfdown.svg
[License]: https://img.shields.io/github/license/markpdfdown/markpdfdown
