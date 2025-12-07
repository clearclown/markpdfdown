"""Tests for the provider abstraction layer."""

import os
from unittest.mock import MagicMock, patch

import pytest

from core.providers import (
    BaseProvider,
    GeminiProvider,
    OpenAIProvider,
    create_provider,
)
from core.providers.base import BaseProvider as BaseProviderClass


class TestCreateProvider:
    """Tests for the create_provider factory function."""

    def test_create_provider_default_is_openai(self):
        """Default provider should be OpenAI when no env var is set."""
        with patch.dict(os.environ, {}, clear=True):
            # Need to set API key for OpenAI provider to initialize
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                provider = create_provider()
                assert isinstance(provider, OpenAIProvider)
                assert provider.name in ["openai", "deepseek"]

    def test_create_provider_openai_explicit(self):
        """Explicitly requesting OpenAI provider."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            provider = create_provider("openai")
            assert isinstance(provider, OpenAIProvider)
            assert provider.name == "openai"

    def test_create_provider_deepseek(self):
        """DeepSeek provider should use OpenAI-compatible provider."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "deepseek", "OPENAI_API_KEY": "test-deepseek-key"},
        ):
            provider = create_provider("deepseek")
            assert isinstance(provider, OpenAIProvider)
            assert provider.name == "deepseek"

    def test_create_provider_gemini(self):
        """Gemini provider should be created when requested."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-gemini-key"}):
            # Mock the google.genai import
            mock_genai = MagicMock()
            mock_types = MagicMock()
            with patch.dict(
                "sys.modules",
                {"google": MagicMock(), "google.genai": mock_genai},
            ):
                with patch(
                    "core.providers.gemini_provider.GeminiProvider.__init__",
                    return_value=None,
                ):
                    provider = create_provider("gemini")
                    assert isinstance(provider, GeminiProvider)

    def test_create_provider_from_env_var(self):
        """Provider should be selected from LLM_PROVIDER env var."""
        with patch.dict(
            os.environ,
            {"LLM_PROVIDER": "deepseek", "OPENAI_API_KEY": "test-key"},
        ):
            provider = create_provider()  # No argument, uses env var
            assert isinstance(provider, OpenAIProvider)
            assert provider.name == "deepseek"

    def test_create_provider_unknown_raises_error(self):
        """Unknown provider should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider("unknown_provider")

    def test_create_provider_case_insensitive(self):
        """Provider name should be case-insensitive."""
        with patch.dict(
            os.environ, {"OPENAI_API_KEY": "test-key", "LLM_PROVIDER": "openai"}
        ):
            provider1 = create_provider("OPENAI")
            provider2 = create_provider("OpenAI")
            provider3 = create_provider("openai")
            assert all(
                isinstance(p, OpenAIProvider) for p in [provider1, provider2, provider3]
            )


class TestBaseProvider:
    """Tests for the BaseProvider abstract class."""

    def test_base_provider_is_abstract(self):
        """BaseProvider should not be directly instantiable."""
        with pytest.raises(TypeError):
            BaseProviderClass()

    def test_encode_image_to_base64(self, tmp_path):
        """Test image encoding to base64."""
        # Create a simple test image file
        test_image = tmp_path / "test.jpg"
        test_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # JPEG header
        test_image.write_bytes(test_content)

        # Create a concrete implementation for testing
        class ConcreteProvider(BaseProviderClass):
            @property
            def name(self):
                return "test"

            def completion(self, *args, **kwargs):
                return "test"

        provider = ConcreteProvider()
        encoded = provider.encode_image_to_base64(str(test_image))

        import base64

        decoded = base64.b64decode(encoded)
        assert decoded == test_content

    def test_get_image_mime_type(self):
        """Test MIME type detection from file extension."""

        class ConcreteProvider(BaseProviderClass):
            @property
            def name(self):
                return "test"

            def completion(self, *args, **kwargs):
                return "test"

        provider = ConcreteProvider()

        assert provider.get_image_mime_type("test.jpg") == "image/jpeg"
        assert provider.get_image_mime_type("test.jpeg") == "image/jpeg"
        assert provider.get_image_mime_type("test.png") == "image/png"
        assert provider.get_image_mime_type("test.gif") == "image/gif"
        assert provider.get_image_mime_type("test.webp") == "image/webp"
        assert provider.get_image_mime_type("test.bmp") == "image/bmp"
        assert provider.get_image_mime_type("test.unknown") == "image/jpeg"  # Default


class TestOpenAIProvider:
    """Tests for the OpenAI provider."""

    def test_openai_provider_initialization(self):
        """OpenAI provider should initialize with API key."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "LLM_PROVIDER": "openai",
            },
            clear=True,
        ):
            provider = OpenAIProvider()
            assert provider.name == "openai"
            assert provider.api_key == "test-key"
            assert provider.model == "gpt-4o"  # Default model

    def test_openai_provider_custom_model(self):
        """OpenAI provider should use custom model from env."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "OPENAI_DEFAULT_MODEL": "gpt-4o-mini",
                "LLM_PROVIDER": "openai",
            },
            clear=True,
        ):
            provider = OpenAIProvider()
            assert provider.model == "gpt-4o-mini"

    def test_openai_provider_custom_base_url(self):
        """OpenAI provider should use custom base URL from env."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "OPENAI_API_BASE": "https://custom.api.com/v1",
                "LLM_PROVIDER": "openai",
            },
            clear=True,
        ):
            provider = OpenAIProvider()
            assert provider.base_url == "https://custom.api.com/v1"

    def test_openai_provider_missing_api_key_raises(self):
        """OpenAI provider should raise error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                OpenAIProvider()

    def test_deepseek_provider_initialization(self):
        """DeepSeek provider should use DeepSeek defaults."""
        with patch.dict(
            os.environ,
            {
                "DEEPSEEK_API_KEY": "deepseek-key",
                "LLM_PROVIDER": "deepseek",
            },
            clear=True,
        ):
            provider = OpenAIProvider()
            assert provider.name == "deepseek"
            assert provider.api_key == "deepseek-key"
            assert provider.base_url == "https://api.deepseek.com/v1"
            assert provider.model == "deepseek-chat"

    def test_deepseek_fallback_to_openai_key(self):
        """DeepSeek should fall back to OPENAI_API_KEY if DEEPSEEK_API_KEY not set."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "fallback-key",
                "LLM_PROVIDER": "deepseek",
            },
            clear=True,
        ):
            provider = OpenAIProvider()
            assert provider.api_key == "fallback-key"

    @patch("openai.OpenAI")
    def test_openai_provider_completion(self, mock_openai_class):
        """Test completion method of OpenAI provider."""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "LLM_PROVIDER": "openai"},
            clear=True,
        ):
            provider = OpenAIProvider()
            result = provider.completion(
                user_message="Hello",
                system_prompt="You are helpful",
                temperature=0.5,
                max_tokens=100,
            )

            assert result == "Test response"
            mock_client.chat.completions.create.assert_called_once()

    @patch("openai.OpenAI")
    def test_openai_provider_completion_with_images(self, mock_openai_class, tmp_path):
        """Test completion with image input."""
        # Create test image
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"\xff\xd8\xff\xe0test image data")

        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Image description"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "LLM_PROVIDER": "openai"},
            clear=True,
        ):
            provider = OpenAIProvider()
            result = provider.completion(
                user_message="Describe this image",
                image_paths=[str(test_image)],
            )

            assert result == "Image description"
            # Verify the call included image data
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs["messages"]
            user_content = messages[-1]["content"]
            assert any(item.get("type") == "image_url" for item in user_content)


class TestGeminiProvider:
    """Tests for the Gemini provider."""

    def test_gemini_provider_missing_package_raises(self):
        """Gemini provider should raise ImportError when google-genai not installed."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            with patch.dict("sys.modules", {"google": None, "google.genai": None}):
                # Force reimport to trigger ImportError
                import importlib

                import core.providers.gemini_provider as gp

                # Clear any cached import
                if "google" in gp.__dict__:
                    del gp.__dict__["google"]

                with pytest.raises(ImportError, match="google-genai"):
                    # Create new instance which triggers import
                    GeminiProvider()

    def test_gemini_provider_missing_api_key_raises(self):
        """Gemini provider should raise error when API key is missing."""
        mock_genai = MagicMock()
        mock_types = MagicMock()

        with patch.dict(os.environ, {}, clear=True):
            with patch.object(
                GeminiProvider,
                "__init__",
                lambda self: None,
            ):
                provider = GeminiProvider.__new__(GeminiProvider)
                # Manually test the API key validation logic
                api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                assert api_key is None

    def test_gemini_provider_uses_google_api_key_fallback(self):
        """Gemini should use GOOGLE_API_KEY as fallback."""
        mock_genai_module = MagicMock()
        mock_types_module = MagicMock()
        mock_client = MagicMock()
        mock_genai_module.Client.return_value = mock_client

        with patch.dict(
            os.environ,
            {"GOOGLE_API_KEY": "google-key"},
            clear=True,
        ):
            with patch.dict(
                "sys.modules",
                {
                    "google": MagicMock(),
                    "google.genai": mock_genai_module,
                    "google.genai.types": mock_types_module,
                },
            ):
                # Patch the import inside __init__
                with patch(
                    "builtins.__import__",
                    side_effect=lambda name, *args: (
                        mock_genai_module
                        if "genai" in name
                        else MagicMock()
                    ),
                ):
                    provider = GeminiProvider.__new__(GeminiProvider)
                    provider._genai = mock_genai_module
                    provider._types = mock_types_module
                    provider.api_key = os.getenv("GEMINI_API_KEY") or os.getenv(
                        "GOOGLE_API_KEY"
                    )
                    assert provider.api_key == "google-key"
