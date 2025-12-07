"""Integration tests for main.py functionality."""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestMainCompletion:
    """Tests for the completion function in main.py."""

    @patch("main.LLMClient")
    def test_completion_function(self, mock_llm_client_class):
        """Test the completion function in main.py."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.completion.return_value = "Generated markdown"
        mock_llm_client_class.return_value = mock_client

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "LLM_PROVIDER": "openai"},
            clear=True,
        ):
            # Reset global client
            import main

            main._llm_client = None

            result = main.completion(
                message="Convert this",
                system_prompt="You are helpful",
                temperature=0.5,
            )

            assert result == "Generated markdown"

    @patch("main.LLMClient")
    def test_completion_with_retry(self, mock_llm_client_class):
        """Test that completion retries on failure."""
        mock_client = MagicMock()
        # Fail twice, then succeed
        mock_client.completion.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            "Success on third try",
        ]
        mock_llm_client_class.return_value = mock_client

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "LLM_PROVIDER": "openai"},
            clear=True,
        ):
            import main

            main._llm_client = None

            with patch("time.sleep"):  # Speed up test
                result = main.completion(
                    message="Test",
                    retry_times=3,
                )

            assert result == "Success on third try"
            assert mock_client.completion.call_count == 3

    @patch("main.LLMClient")
    def test_completion_all_retries_fail(self, mock_llm_client_class):
        """Test that completion returns empty string after all retries fail."""
        mock_client = MagicMock()
        mock_client.completion.side_effect = Exception("Always fails")
        mock_llm_client_class.return_value = mock_client

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "LLM_PROVIDER": "openai"},
            clear=True,
        ):
            import main

            main._llm_client = None

            with patch("time.sleep"):
                result = main.completion(
                    message="Test",
                    retry_times=3,
                )

            assert result == ""
            assert mock_client.completion.call_count == 3

    @patch("main.LLMClient")
    def test_get_llm_client_singleton(self, mock_llm_client_class):
        """Test that get_llm_client returns singleton instance."""
        mock_client = MagicMock()
        mock_llm_client_class.return_value = mock_client

        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "LLM_PROVIDER": "openai"},
            clear=True,
        ):
            import main

            main._llm_client = None

            client1 = main.get_llm_client()
            client2 = main.get_llm_client()

            assert client1 is client2
            # Should only be called once
            assert mock_llm_client_class.call_count == 1


class TestConvertImageToMarkdown:
    """Tests for convert_image_to_markdown function."""

    @patch("main.completion")
    def test_convert_image_to_markdown(self, mock_completion, tmp_path):
        """Test image to markdown conversion."""
        # Create test image
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"\xff\xd8\xff\xe0test")

        mock_completion.return_value = "```markdown\n# Heading\nContent\n```"

        from main import convert_image_to_markdown

        result = convert_image_to_markdown(str(test_image))

        # Should strip markdown wrapper
        assert result == "# Heading\nContent"
        mock_completion.assert_called_once()

        # Check that image path was passed
        call_kwargs = mock_completion.call_args.kwargs
        assert str(test_image) in call_kwargs["image_paths"]

    @patch("main.completion")
    def test_convert_image_preserves_content(self, mock_completion):
        """Test that content is preserved without wrapper."""
        mock_completion.return_value = "# Title\n\nSome content with **bold** text."

        from main import convert_image_to_markdown

        result = convert_image_to_markdown("/fake/path.jpg")

        # Should return as-is since there's no markdown wrapper
        assert "# Title" in result
        assert "**bold**" in result


class TestProviderSwitching:
    """Tests for switching between providers."""

    def test_switch_to_deepseek(self):
        """Test switching to DeepSeek provider."""
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "deepseek",
                "DEEPSEEK_API_KEY": "deepseek-key",
            },
            clear=True,
        ):
            import main
            main._llm_client = None

            client = main.get_llm_client()
            assert client.provider.name == "deepseek"

    def test_switch_to_openai(self):
        """Test switching to OpenAI provider."""
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "openai",
                "OPENAI_API_KEY": "openai-key",
            },
            clear=True,
        ):
            import main
            main._llm_client = None

            client = main.get_llm_client()
            assert client.provider.name == "openai"

    def test_default_provider_is_openai(self):
        """Test that default provider is OpenAI."""
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
            },
            clear=True,
        ):
            import main
            main._llm_client = None

            client = main.get_llm_client()
            assert client.provider.name == "openai"
