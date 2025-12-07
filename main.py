import logging
import os
import shutil
import sys
import time

from dotenv import load_dotenv

from core.FileWorker import create_worker
from core.LLMClient import LLMClient
from core.Util import remove_markdown_warp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

load_dotenv()

# Global LLM client instance (initialized once)
_llm_client = None


def get_llm_client() -> LLMClient:
    """
    Get or create the global LLM client instance.
    Uses LLM_PROVIDER environment variable to select provider.

    Supported providers:
        - openai: OpenAI API (default)
        - deepseek: DeepSeek API (OpenAI-compatible)
        - gemini: Google Gemini API

    Returns:
        LLMClient: Configured LLM client
    """
    global _llm_client
    if _llm_client is None:
        provider_name = os.getenv("LLM_PROVIDER", "openai").lower()
        logger.info(f"Initializing LLM client with provider: {provider_name}")
        _llm_client = LLMClient(provider_name=provider_name)
    return _llm_client


def completion(
    message,
    system_prompt="",
    image_paths=None,
    temperature=0.5,
    max_tokens=8192,
    retry_times=3,
):
    """
    Call LLM completion interface for text generation.

    Args:
        message (str): User input message
        system_prompt (str, optional): System prompt, defaults to empty string
        image_paths (List[str], optional): List of image paths, defaults to None
        temperature (float, optional): Temperature for text generation, defaults to 0.5
        max_tokens (int, optional): Maximum number of tokens for generated text, defaults to 8192
        retry_times (int, optional): Number of retry attempts, defaults to 3

    Returns:
        str: Generated text content
    """
    client = get_llm_client()

    # Call completion method with retry mechanism
    for attempt in range(retry_times):
        try:
            response = client.completion(
                user_message=message,
                system_prompt=system_prompt,
                image_paths=image_paths,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response
        except Exception as e:
            logger.error(f"LLM call failed (attempt {attempt + 1}/{retry_times}): {e}")
            if attempt < retry_times - 1:
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
    return ""


def convert_image_to_markdown(image_path):
    """
    Convert image to Markdown format
    Args:
        image_path (str): Path to the image
    Returns:
        str: Converted Markdown string
    """
    system_prompt = """
You are a helpful assistant that can convert images to Markdown format. You are given an image, and you need to convert it to Markdown format. Please output the Markdown content only, without any other text.
"""
    user_prompt = """
Below is the image of one page of a document, please read the content in the image and transcribe it into plain Markdown format. Please note:
1. Identify heading levels, text styles, formulas, and the format of table rows and columns
2. Mathematical formulas should be transcribed using LaTeX syntax, ensuring consistency with the original
3. Please output the Markdown content only, without any other text.

Output Example:
```markdown
{example}
```
"""

    response = completion(
        message=user_prompt,
        system_prompt=system_prompt,
        image_paths=[image_path],
        temperature=0.3,
        max_tokens=8192,
    )
    response = remove_markdown_warp(response, "markdown")
    return response


if __name__ == "__main__":
    start_page = 1
    end_page = 0
    if len(sys.argv) > 2:
        start_page = int(sys.argv[1])
        end_page = int(sys.argv[2])
    elif len(sys.argv) > 1:
        start_page = 1
        end_page = int(sys.argv[1])

    # Read binary data from standard input
    input_data = sys.stdin.buffer.read()
    if not input_data:
        logger.error("No input data received")
        logger.error(
            "Usage: python main.py [start_page] [end_page] < path_to_input.pdf"
        )
        exit(1)

    # Create output directory
    output_dir = f"output/{time.strftime('%Y%m%d%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)

    # Try to get extension from file name
    input_filename = os.path.basename(sys.stdin.buffer.name)
    input_ext = os.path.splitext(input_filename)[1]

    # If there is no extension or the file comes from standard input, try to determine the type by file content
    if not input_ext or input_filename == "<stdin>":
        # PDF file magic number/signature is %PDF-
        if input_data.startswith(b"%PDF-"):
            input_ext = ".pdf"
            logger.info("Recognized as PDF file by file content")
        # JPEG file magic number/signature is FF D8 FF DB
        elif input_data.startswith(b"\xff\xd8\xff\xdb"):
            input_ext = ".jpeg"
            logger.info("Recognized as JPEG file by file content")
        # JPG file magic number/signature is FF D8 FF E0
        elif input_data.startswith(b"\xff\xd8\xff\xe0"):
            input_ext = ".jpg"
            logger.info("Recognized as JPG file by file content")
        # PNG file magic number/signature is 89 50 4E 47
        elif input_data.startswith(b"\x89\x50\x4e\x47"):
            input_ext = ".png"
            logger.info("Recognized as PNG file by file content")
        # BMP file magic number/signature is 42 4D
        elif input_data.startswith(b"\x42\x4d"):
            input_ext = ".bmp"
            logger.info("Recognized as BMP file by file content")
        else:
            logger.error("Unsupported file type")
            exit(1)

    input_path = os.path.join(output_dir, f"input{input_ext}")
    with open(input_path, "wb") as f:
        f.write(input_data)

    # create file worker
    try:
        worker = create_worker(input_path, start_page, end_page)
    except ValueError as e:
        logger.error(str(e))
        exit(1)

    # convert to images
    img_paths = worker.convert_to_images()
    logger.info("Image conversion completed")

    # convert to markdown
    markdown = ""
    for img_path in sorted(img_paths):
        img_path = img_path.replace("\\", "/")
        logger.info("Converting image %s to Markdown", img_path)
        content = convert_image_to_markdown(img_path)
        if content:
            # 写入文件
            with open(
                os.path.join(output_dir, f"{os.path.basename(img_path)}.md"), "w"
            ) as f:
                f.write(content)
            markdown += content
            markdown += "\n\n"

    # Output Markdown
    print(markdown)
    logger.info("Image conversion to Markdown completed")
    # Remote output path
    shutil.rmtree(output_dir)
    exit(0)
