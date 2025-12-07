import logging
from typing import Optional

from .providers import BaseProvider, create_provider

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified LLM client that supports multiple providers.
    Supports: OpenAI, DeepSeek, Google Gemini
    """

    def __init__(
        self,
        provider: Optional[BaseProvider] = None,
        provider_name: Optional[str] = None,
        # Legacy parameters for backwards compatibility
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize LLM client.

        Args:
            provider: Pre-configured provider instance
            provider_name: Provider name ("openai", "deepseek", "gemini")
            base_url: (Legacy) Base URL for OpenAI-compatible API
            api_key: (Legacy) API key
            model: (Legacy) Model name
        """
        if provider is not None:
            self._provider = provider
        else:
            # Create provider based on name or environment
            self._provider = create_provider(provider_name)

        logger.info(f"LLMClient initialized with provider: {self._provider.name}")

    @property
    def provider(self) -> BaseProvider:
        """Get the current provider."""
        return self._provider

    def completion(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        image_paths: Optional[list[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        """
        Create chat completion (supports multimodal).

        Args:
            user_message: User message content
            system_prompt: System prompt (optional)
            image_paths: List of image paths (optional)
            temperature: Generation temperature
            max_tokens: Maximum number of tokens

        Returns:
            str: Model generated response content
        """
        return self._provider.completion(
            user_message=user_message,
            system_prompt=system_prompt,
            image_paths=image_paths,
            temperature=temperature,
            max_tokens=max_tokens,
        )
