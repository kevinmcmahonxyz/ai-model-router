"""Token estimation service for cost prediction."""
from typing import List, Dict
import tiktoken


class TokenEstimator:
    """Estimate token counts before sending requests to providers."""
    
    # Safety buffer to account for estimation inaccuracy
    BUFFER_MULTIPLIER = 1.15  # Add 15% buffer
    
    def __init__(self):
        """Initialize with default encoding."""
        # cl100k_base is used by gpt-4, gpt-3.5-turbo, and most modern models
        self.default_encoding = tiktoken.get_encoding("cl100k_base")
    
    def _get_encoding_for_model(self, model_id: str) -> tiktoken.Encoding:
        """
        Get the appropriate encoding for a model.
        
        Args:
            model_id: Model identifier (e.g., 'gpt-4o-mini')
        
        Returns:
            tiktoken.Encoding object
        """
        try:
            return tiktoken.encoding_for_model(model_id)
        except KeyError:
            # Model not recognized, use default
            return self.default_encoding
    
    def estimate_messages_tokens(
        self,
        messages: List[Dict[str, str]],
        model_id: str = "gpt-4o-mini"
    ) -> Dict[str, int]:
        """
        Estimate token count for a list of messages.
        
        This matches OpenAI's token counting logic:
        - Each message has overhead (role, formatting)
        - Content is tokenized
        - Reply priming adds tokens
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model_id: Model ID for tokenizer selection
        
        Returns:
            Dict with 'estimated_tokens' and 'buffered_tokens'
        """
        encoding = self._get_encoding_for_model(model_id)
        
        # Token overhead per message
        # Format: <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 3
        tokens_per_name = 1
        
        num_tokens = 0
        
        for message in messages:
            num_tokens += tokens_per_message
            
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        
        # Every reply is primed with <|start|>assistant<|message|>
        num_tokens += 3
        
        # Add safety buffer
        buffered_tokens = int(num_tokens * self.BUFFER_MULTIPLIER)
        
        return {
            "estimated_tokens": num_tokens,
            "buffered_tokens": buffered_tokens
        }
    
    def estimate_cost(
        self,
        messages: List[Dict[str, str]],
        model_id: str,
        input_price_per_1m: float,
        output_price_per_1m: float,
        expected_output_tokens: int = 500
    ) -> Dict[str, float]:
        """
        Estimate cost for a request before sending it.
        
        Args:
            messages: List of message dicts
            model_id: Model ID
            input_price_per_1m: Price per 1M input tokens
            output_price_per_1m: Price per 1M output tokens
            expected_output_tokens: Estimated response length (default 500)
        
        Returns:
            Dict with cost estimates in USD
        """
        # Estimate input tokens
        token_estimate = self.estimate_messages_tokens(messages, model_id)
        input_tokens = token_estimate["buffered_tokens"]
        
        # Use provided output estimate (could be smarter in future)
        output_tokens = expected_output_tokens
        
        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * input_price_per_1m
        output_cost = (output_tokens / 1_000_000) * output_price_per_1m
        total_cost = input_cost + output_cost
        
        return {
            "estimated_input_tokens": input_tokens,
            "estimated_output_tokens": output_tokens,
            "estimated_total_tokens": input_tokens + output_tokens,
            "estimated_input_cost_usd": round(input_cost, 8),
            "estimated_output_cost_usd": round(output_cost, 8),
            "estimated_total_cost_usd": round(total_cost, 8)
        }