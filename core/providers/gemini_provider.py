import logging
import os
from typing import Optional

from .base import BaseProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    """
    Google Gemini provider using the google-genai SDK.
    """

    def __init__(self):
        """Initialize the Gemini provider."""
        # Import here to make it optional dependency
        try:
            from google import genai
            from google.genai import types

            self._genai = genai
            self._types = types
        except ImportError as e:
            raise ImportError(
                "google-genai package is required for Gemini provider. "
                "Install it with: pip install google-genai"
            ) from e

        # Get API key
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Set GEMINI_API_KEY or GOOGLE_API_KEY.")

        # Get model (allow override via environment variable)
        self.model = os.getenv("GEMINI_MODEL") or os.getenv(
            "OPENAI_DEFAULT_MODEL", "gemini-2.5-flash"
        )

        # Initialize client
        self.client = self._genai.Client(api_key=self.api_key)

        logger.info(f"Initialized Gemini provider with model: {self.model}")

    @property
    def name(self) -> str:
        return "gemini"

    def completion(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        image_paths: Optional[list[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        """
        Generate a completion using Google Gemini API.

        Args:
            user_message: The user's message/prompt
            system_prompt: Optional system prompt
            image_paths: Optional list of image file paths
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            str: Generated text response
        """
        # Build content parts
        contents = []

        # Add images first (if any)
        if image_paths:
            for img_path in image_paths:
                with open(img_path, "rb") as f:
                    image_bytes = f.read()
                mime_type = self.get_image_mime_type(img_path)
                contents.append(
                    self._types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                )

        # Add text message
        contents.append(user_message)

        # Build generation config
        generation_config = self._types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        # Add system instruction if provided
        if system_prompt:
            generation_config.system_instruction = system_prompt

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generation_config,
            )
            return response.text

        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
            raise
