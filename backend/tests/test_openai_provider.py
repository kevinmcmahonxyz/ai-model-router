"""Tests for OpenAI provider with mocked API calls."""
import pytest
import responses
from unittest.mock import patch, MagicMock
from src.providers.openai_provider import OpenAIProvider


class TestOpenAIProvider:
    """Test OpenAI provider with mocked API responses."""
    
    @pytest.fixture
    def provider(self):
        """Create provider instance."""
        return OpenAIProvider()
    
    @pytest.mark.asyncio
    async def test_successful_request(self, provider):
        """Test successful API call with mocked OpenAI client."""
        # Mock the OpenAI client response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! How can I assist you today?"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 9
        mock_response.usage.total_tokens = 19
        mock_response.model = "gpt-4o-mini"
        
        # Patch the OpenAI client
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response):
            messages = [{"role": "user", "content": "Hello!"}]
            result = await provider.send_request(
                messages=messages,
                model="gpt-4o-mini"
            )
        
        # Verify response structure
        assert result["success"] is True
        assert result["content"] == "Hello! How can I assist you today?"
        assert result["finish_reason"] == "stop"
        assert result["usage"]["input_tokens"] == 10
        assert result["usage"]["output_tokens"] == 9
        assert result["usage"]["total_tokens"] == 19
        assert result["model"] == "gpt-4o-mini"
        assert result["error"] is None
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, provider):
        """Test handling of API errors."""
        # Mock an exception from OpenAI
        with patch.object(
            provider.client.chat.completions,
            'create',
            side_effect=Exception("API Error: Internal server error")
        ):
            messages = [{"role": "user", "content": "Test"}]
            result = await provider.send_request(
                messages=messages,
                model="gpt-4o-mini"
            )
        
        # Should return error dict, not raise exception
        assert result["success"] is False
        assert result["content"] is None
        assert result["error"] is not None
        assert "API Error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_missing_choices(self, provider):
        """Test handling when API returns no choices."""
        # Mock response with no choices
        mock_response = MagicMock()
        mock_response.choices = []
        
        with patch.object(provider.client.chat.completions, 'create', return_value=mock_response):
            messages = [{"role": "user", "content": "Test"}]
            result = await provider.send_request(
                messages=messages,
                model="gpt-4o-mini"
            )
        
        # Should handle gracefully
        assert result["success"] is False
        assert "No choices returned" in result["error"]
    
    def test_token_counting(self, provider):
        """Test token counting accuracy."""
        text = "Hello, world!"
        tokens = provider.count_tokens(text, model="gpt-4o-mini")
        
        # Should return a positive integer
        assert isinstance(tokens, int)
        assert tokens > 0
        
        # Longer text should have more tokens
        longer_text = "Hello, world! " * 10
        longer_tokens = provider.count_tokens(longer_text, model="gpt-4o-mini")
        assert longer_tokens > tokens
    
    def test_token_counting_empty_string(self, provider):
        """Test token counting with empty string."""
        tokens = provider.count_tokens("", model="gpt-4o-mini")
        assert tokens == 0
    
    def test_count_messages_tokens(self, provider):
        """Test counting tokens for messages with overhead."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]
        
        tokens = provider.count_messages_tokens(messages, model="gpt-4o-mini")
        
        # Should include message overhead (3 tokens per message + 3 for reply)
        assert isinstance(tokens, int)
        assert tokens > 10  # More than just content tokens