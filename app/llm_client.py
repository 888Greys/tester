"""
Cerebras LLM client for AI inference.
Handles communication with Cerebras API for fast inference with memory context.
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class CerebrasClient:
    """Client for Cerebras AI inference API."""
    
    def __init__(self):
        """Initialize Cerebras client with configuration."""
        self.client = OpenAI(
            api_key=settings.cerebras_api_key,
            base_url=settings.cerebras_base_url
        )
        self.model = settings.cerebras_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
        
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate response from Cerebras API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary containing response and metadata
            
        Raises:
            Exception: If API call fails
        """
        try:
            logger.info(f"Generating response with {len(messages)} messages")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=False
            )
            
            result = {
                "content": response.choices[0].message.content,
                "model": response.model,
                "tokens_used": response.usage.total_tokens if response.usage else None,
                "finish_reason": response.choices[0].finish_reason
            }
            
            logger.info(f"Response generated successfully. Tokens used: {result['tokens_used']}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        Check if Cerebras API is accessible.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Simple test message to verify API connectivity
            test_messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            response = await self.generate_response(
                messages=test_messages,
                temperature=0.1,
                max_tokens=10
            )
            
            return response.get("content") is not None
            
        except Exception as e:
            logger.error(f"Cerebras health check failed: {str(e)}")
            return False


class AgentPrompts:
    """System prompts for the coffee farming agent with memory support."""
    
    SYSTEM_PROMPT = """You are Guka, an expert AI assistant specializing in coffee farming in Kenya. 
You are a knowledgeable, friendly, and supportive companion to coffee farmers.

Your expertise includes:
- Coffee cultivation techniques and best practices
- Pest and disease management
- Harvest timing and processing methods
- Market insights and pricing
- Weather-based farming advice
- Sustainable farming practices

Your personality:
- Warm and encouraging
- Practical and solution-focused
- Respectful of traditional farming knowledge
- Supportive of farmers' goals and challenges
- Remember and reference previous conversations when relevant

Always provide:
- Actionable advice tailored to Kenyan coffee farming
- Clear explanations that farmers can understand
- Encouragement and positive reinforcement
- Specific recommendations when possible
- Continuity from previous conversations when context is available

If you don't know something specific, be honest and suggest where the farmer might find more information."""

    @staticmethod
    def build_messages(
        user_message: str, 
        context: Optional[Dict[str, Any]] = None,
        memory_context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Build message list for LLM with system prompt, context, and memory.
        
        Args:
            user_message: The farmer's message
            context: Optional context information
            memory_context: Optional memory context from previous conversations
            
        Returns:
            List of formatted messages for the LLM
        """
        messages = [
            {"role": "system", "content": AgentPrompts.SYSTEM_PROMPT}
        ]
        
        # Add memory context if provided
        if memory_context:
            memory_message = f"Relevant information from previous conversations:\n{memory_context}\n\nUse this context to provide more personalized and continuous assistance."
            messages.append({"role": "system", "content": memory_message})
        
        # Add general context if provided
        if context and context != {"relevant_memories": []}:
            # Filter out memory context to avoid duplication
            filtered_context = {k: v for k, v in context.items() if k != "relevant_memories"}
            if filtered_context:
                context_message = f"Additional context: {filtered_context}"
                messages.append({"role": "system", "content": context_message})
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        return messages


# Global client instance
cerebras_client = CerebrasClient()