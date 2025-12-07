import logging
import os
from typing import Optional

import openai

from .base import BaseProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """
    OpenAI-compatible provider.
    Works with OpenAI, DeepSeek, and other OpenAI-compatible APIs.
    """

    # Default configurations for different services
    PROVIDER_CONFIGS = {
        "openai": {
            "base_url": "https://api.openai.com/v1/",
            "default_model": "gpt-4o",
            "env_key": "OPENAI_API_KEY",
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "default_model": "deepseek-chat",
            "env_key": "DEEPSEEK_API_KEY",
        },
    }

    def __init__(self):
        """Initialize the OpenAI-compatible provider."""
        self._provider_type = os.getenv("LLM_PROVIDER", "openai").lower()
        if self._provider_type not in self.PROVIDER_CONFIGS:
            self._provider_type = "openai"

        config = self.PROVIDER_CONFIGS[self._provider_type]

        # Get API key (check provider-specific key first, then fall back to OPENAI_API_KEY)
        self.api_key = os.getenv(config["env_key"]) or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                f"API key not found. Set {config['env_key']} or OPENAI_API_KEY."
            )

        # Get base URL (allow override via environment variable)
        self.base_url = os.getenv("OPENAI_API_BASE") or config["base_url"]

        # Get model (allow override via environment variable)
        self.model = os.getenv("OPENAI_DEFAULT_MODEL") or config["default_model"]

        # Initialize client
        self.client = openai.OpenAI(base_url=self.base_url, api_key=self.api_key)

        logger.info(
            f"Initialized {self._provider_type} provider with model: {self.model}"
        )

    @property
    def name(self) -> str:
        return self._provider_type

    def completion(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        image_paths: Optional[list[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        """
        Generate a completion using OpenAI-compatible API.

        Args:
            user_message: The user's message/prompt
            system_prompt: Optional system prompt
            image_paths: Optional list of image file paths
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            str: Generated text response
        """
        # Build user content with text and optional images
        user_content = [{"type": "text", "text": user_message}]

        if image_paths:
            for img_path in image_paths:
                base64_image = self.encode_image_to_base64(img_path)
                mime_type = self.get_image_mime_type(img_path)
                user_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                    }
                )

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_headers={
                    "X-Title": "MarkPDFdown",
                    "HTTP-Referer": "https://github.com/MarkPDFdown/markpdfdown.git",
                },
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise
