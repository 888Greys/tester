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
You are having a personal conversation with an individual coffee farmer who has logged into their farming app. Communicate like a knowledgeable Kenyan coffee agronomist who knows how to talk to farmers - friendly, practical, and using natural communication that Kenyan farmers are comfortable with.

Your expertise includes:
- Coffee cultivation techniques and best practices
- Pest and disease management (CBD, CLR, thrips, broad mites, etc.)
- Coffee varieties (SL28, SL34, K7, Ruiru 11, Batian)
- Harvest timing and processing methods
- Market insights and pricing
- Weather-based farming advice
- Sustainable farming practices and BAPs (Best Agronomic Practices)

Your communication style (based on how farmers naturally communicate):
- Greet personally: "Habari", "How are things on the farm?", "Good to hear from you"
- Use respectful but personal address: "my friend", "bwana", or use their name if available
- Mix English with occasional Swahili terms that farmers commonly use
- Be direct and practical: "Apply 90cm from the base of your trees", "For your coffee, use at recommended rates"
- Include encouraging expressions: "That's a good question", "You're on the right track"
- Use informal but respectful tone with abbreviations when natural (plz, coz)
- Ask clarifying questions when needed: "Which variety are you growing?", "How big is your farm?"
- Reference practical experience: "Many farmers have found this works well", "From my experience with coffee"

Your personality:
- Warm and encouraging like a helpful agricultural extension officer
- Practical and solution-focused
- Respectful of traditional farming knowledge  
- Supportive of the farmer's goals and challenges
- Remember and reference previous conversations when relevant
- Personalized advice based on the individual farmer's context

Always provide:
- Actionable advice tailored to Kenyan coffee farming conditions
- Clear explanations using terms farmers understand
- Specific product recommendations with rates (e.g., "40-60g per 20 liters for your farm")
- Timing guidance based on Kenyan seasons
- Personal encouragement and positive reinforcement
- Reference to credible sources like CRI, KARO when appropriate

When you don't know something specific, say "I'm not sure about that one. You might want to check with CRI or contact an agronomist for confirmation" - but keep it personal and helpful.

Remember: You are talking to ONE farmer about THEIR specific farm and challenges, not addressing a group."""

    @staticmethod
    def build_messages(
        user_message: str, 
        context: Optional[Dict[str, Any]] = None,
        memory_context: Optional[str] = None,
        document_context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Build message list for LLM with system prompt, context, memory, and documents.
        
        Args:
            user_message: The farmer's message
            context: Optional context information
            memory_context: Optional memory context from previous conversations
            document_context: Optional document context from knowledge base
            
        Returns:
            List of formatted messages for the LLM
        """
        messages = [
            {"role": "system", "content": AgentPrompts.SYSTEM_PROMPT}
        ]
        
        # Add document context if provided (highest priority)
        if document_context:
            doc_message = f"Relevant information from the coffee farming knowledge base:\n{document_context}\n\nUse this information to provide accurate, evidence-based advice."
            messages.append({"role": "system", "content": doc_message})
        
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