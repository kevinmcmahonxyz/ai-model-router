"""Base provider interface for LLM providers."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All provider implementations (OpenAI, Anthropic, etc.) must inherit
    from this class and implement these methods.
    
    This ensures consistent interface across all providers, making it
    easy to add new providers and switch between them.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize provider with API key.
        
        Args:
            api_key: API key for the provider
        """
        self.api_key = api_key
    
    @abstractmethod
    async def send_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request to provider.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model ID (provider-specific)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Standardized dict with:
            {
                "success": bool,
                "content": str or None,
                "finish_reason": str or None,
                "usage": {
                    "input_tokens": int,
                    "output_tokens": int,
                    "total_tokens": int
                } or None,
                "latency_ms": int,
                "model": str,
                "error": str or None
            }
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text for a specific model.
        
        Different providers use different tokenization methods,
        so each provider implements its own logic.
        
        Args:
            text: Text to count tokens for
            model: Model name (affects tokenization)
        
        Returns:
            Number of tokens
        """
        pass
    
    @abstractmethod
    def count_messages_tokens(
        self,
        messages: List[Dict[str, str]],
        model: str
    ) -> int:
        """
        Count tokens for a list of messages.
        
        Includes overhead for message formatting, which varies
        by provider.
        
        Args:
            messages: List of message dicts
            model: Model name
        
        Returns:
            Total token count
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Return the provider name (e.g., 'openai', 'anthropic').
        
        Used for logging and routing.
        """
        pass