from .base import BaseProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider

__all__ = ["BaseProvider", "OpenAIProvider", "GeminiProvider", "create_provider"]


def create_provider(provider_name: str = None) -> BaseProvider:
    """
    Create a provider instance based on the provider name.

    Args:
        provider_name: Provider name ("openai", "gemini", "deepseek").
                      If None, uses LLM_PROVIDER env var or defaults to "openai".

    Returns:
        BaseProvider: Provider instance
    """
    import os

    if provider_name is None:
        provider_name = os.getenv("LLM_PROVIDER", "openai").lower()
    else:
        provider_name = provider_name.lower()

    providers = {
        "openai": OpenAIProvider,
        "deepseek": OpenAIProvider,  # DeepSeek uses OpenAI-compatible API
        "gemini": GeminiProvider,
    }

    if provider_name not in providers:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Supported providers: {list(providers.keys())}"
        )

    return providers[provider_name]()
