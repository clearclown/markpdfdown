"""Tests for the LLMClient unified interface."""

import os
from unittest.mock import MagicMock, patch

import pytest

from core.LLMClient import LLMClient
from core.providers import OpenAIProvider
from core.providers.base import BaseProvider


class MockProvider(BaseProvider):
    """Mock provider for testing."""

    def __init__(self, response: str = "Mock response"):
        self._response = response
        self._calls = []

    @property
    def name(self) -> str:
        return "mock"

    def completion(
        self,
        user_message: str,
        system_prompt: str = None,
        image_paths: list = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        self._calls.append(
            {
                "user_message": user_message,
                "system_prompt": system_prompt,
                "image_paths": image_paths,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        return self._response


class TestLLMClient:
    """Tests for LLMClient class."""

    def test_llm_client_with_provider_instance(self):
        """LLMClient should accept a pre-configured provider."""
        mock_provider = MockProvider("Custom response")
        client = LLMClient(provider=mock_provider)

        assert client.provider.name == "mock"
        result = client.completion("Hello")
        assert result == "Custom response"

    def test_llm_client_with_provider_name(self):
        """LLMClient should create provider by name."""
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "LLM_PROVIDER": "openai"},
            clear=True,
        ):
            client = LLMClient(provider_name="openai")
            assert isinstance(client.provider, OpenAIProvider)

    def test_llm_client_default_provider(self):
        """LLMClient should use default provider from env."""
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "LLM_PROVIDER": "openai"},
            clear=True,
        ):
            client = LLMClient()
            assert isinstance(client.provider, OpenAIProvider)

    def test_llm_client_completion_passes_params(self):
        """LLMClient should pass all parameters to provider."""
        mock_provider = MockProvider()
        client = LLMClient(provider=mock_provider)

        client.completion(
            user_message="Test message",
            system_prompt="System prompt",
            image_paths=["/path/to/image.jpg"],
            temperature=0.5,
            max_tokens=1000,
        )

        assert len(mock_provider._calls) == 1
        call = mock_provider._calls[0]
        assert call["user_message"] == "Test message"
        assert call["system_prompt"] == "System prompt"
        assert call["image_paths"] == ["/path/to/image.jpg"]
        assert call["temperature"] == 0.5
        assert call["max_tokens"] == 1000

    def test_llm_client_provider_property(self):
        """LLMClient should expose provider via property."""
        mock_provider = MockProvider()
        client = LLMClient(provider=mock_provider)

        assert client.provider is mock_provider

    def test_llm_client_multiple_completions(self):
        """LLMClient should handle multiple completion calls."""
        mock_provider = MockProvider("Response")
        client = LLMClient(provider=mock_provider)

        result1 = client.completion("First message")
        result2 = client.completion("Second message")
        result3 = client.completion("Third message")

        assert result1 == result2 == result3 == "Response"
        assert len(mock_provider._calls) == 3

    def test_llm_client_with_deepseek(self):
        """LLMClient should work with DeepSeek provider."""
        with patch.dict(
            os.environ,
            {
                "DEEPSEEK_API_KEY": "deepseek-key",
                "LLM_PROVIDER": "deepseek",
            },
            clear=True,
        ):
            client = LLMClient(provider_name="deepseek")
            assert client.provider.name == "deepseek"
            assert isinstance(client.provider, OpenAIProvider)


class TestLLMClientIntegration:
    """Integration tests for LLMClient with mocked API calls."""

    @patch("openai.OpenAI")
    def test_full_completion_flow(self, mock_openai_class):
        """Test complete flow from LLMClient to API."""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "API Response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "LLM_PROVIDER": "openai"},
            clear=True,
        ):
            client = LLMClient()
            result = client.completion(
                user_message="Hello, world!",
                system_prompt="Be helpful",
                temperature=0.3,
            )

            assert result == "API Response"

    @patch("openai.OpenAI")
    def test_completion_with_image_flow(self, mock_openai_class, tmp_path):
        """Test completion with image through full flow."""
        # Create test image
        test_image = tmp_path / "test.png"
        test_image.write_bytes(b"\x89PNG\r\n\x1a\ntest data")

        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Image analyzed"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "LLM_PROVIDER": "openai"},
            clear=True,
        ):
            client = LLMClient()
            result = client.completion(
                user_message="What is in this image?",
                image_paths=[str(test_image)],
            )

            assert result == "Image analyzed"

            # Verify image was included in request
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs["messages"]
            user_content = messages[-1]["content"]

            # Should have text and image_url parts
            has_text = any(item.get("type") == "text" for item in user_content)
            has_image = any(item.get("type") == "image_url" for item in user_content)
            assert has_text and has_image

    @patch("openai.OpenAI")
    def test_error_handling(self, mock_openai_class):
        """Test that errors from API are properly raised."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "LLM_PROVIDER": "openai"},
            clear=True,
        ):
            client = LLMClient()
            with pytest.raises(Exception, match="API Error"):
                client.completion(user_message="Test")
