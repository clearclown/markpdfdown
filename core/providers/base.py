import base64
import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """
    Abstract base class for LLM providers.
    All providers must implement the completion method.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass

    @abstractmethod
    def completion(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        image_paths: Optional[list[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        """
        Generate a completion from the LLM.

        Args:
            user_message: The user's message/prompt
            system_prompt: Optional system prompt
            image_paths: Optional list of image file paths for multimodal input
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in the response

        Returns:
            str: The generated text response
        """
        pass

    def encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode an image file to base64 string.

        Args:
            image_path: Path to the image file

        Returns:
            str: Base64 encoded image data
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def get_image_mime_type(self, image_path: str) -> str:
        """
        Get the MIME type of an image based on file extension.

        Args:
            image_path: Path to the image file

        Returns:
            str: MIME type string
        """
        import os

        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        return mime_types.get(ext, "image/jpeg")
