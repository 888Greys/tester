"""
Core agent service for chat interactions.
Enhanced with memory context integration and document search (RAG).
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.llm_client import cerebras_client, AgentPrompts
from app.models.api_models import ChatRequest, ChatResponse
from app.config import settings

logger = logging.getLogger(__name__)


class AgentService:
    """Core agent service handling chat interactions with memory context and document search."""
    
    def __init__(self):
        """Initialize the agent service."""
        self.llm_client = cerebras_client
        # Import here to avoid circular imports
        from app.services.document_service import document_service
        from app.services.weather_service import weather_service
        self.document_service = document_service
        self.weather_service = weather_service
        
    async def process_chat_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process a chat message and generate response with memory context and document search.
        
        Args:
            request: Chat request containing message and context
            
        Returns:
            Chat response with agent's reply
            
        Raises:
            Exception: If processing fails
        """
        try:
            # Generate session ID if not provided
            session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
            
            logger.info(f"Processing chat message for session: {session_id}")
            
            # Extract relevant memories from context
            relevant_memories = request.context.get("relevant_memories", []) if request.context else []
            
            # Search relevant documents for the user's question
            document_context = await self._search_relevant_documents(request.message, request.user_id)
            
            # Get weather context if user has location data
            weather_context = await self._get_weather_context(request.context, request.message)
            
            # Build enhanced context with memory, documents, and weather
            memory_context = self._build_memory_context(relevant_memories)
            
            # Build messages for LLM with memory, document, and weather context
            messages = AgentPrompts.build_messages(
                user_message=request.message,
                context=request.context,
                memory_context=memory_context,
                document_context=document_context,
                weather_context=weather_context
            )
            
            # Generate response from Cerebras
            llm_response = await self.llm_client.generate_response(messages)
            
            # Create response object
            response = ChatResponse(
                response=llm_response["content"],
                session_id=session_id,
                model_used=llm_response["model"],
                tokens_used=llm_response["tokens_used"]
            )
            
            logger.info(f"Chat response generated for session: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            raise Exception(f"Failed to process chat message: {str(e)}")
    
    def _build_memory_context(self, relevant_memories: list) -> str:
        """
        Build memory context string from relevant memories.
        
        Args:
            relevant_memories: List of relevant memory items
            
        Returns:
            Formatted memory context string
        """
        if not relevant_memories:
            return ""
        
        memory_parts = []
        memory_parts.append("Previous conversation context:")
        
        for i, memory in enumerate(relevant_memories[:3], 1):  # Limit to top 3
            content = memory.get("content", "")
            similarity = memory.get("similarity_score", 0)
            
            if content and similarity > 0.7:  # Only include high-confidence memories
                memory_parts.append(f"{i}. {content} (relevance: {similarity:.2f})")
        
        return "\n".join(memory_parts) if len(memory_parts) > 1 else ""
    
    async def _search_relevant_documents(self, query: str, user_id: Optional[str] = None) -> str:
        """
        Search for relevant documents to answer the user's question.
        
        Args:
            query: User's question/message
            user_id: User ID for filtering documents
            
        Returns:
            Formatted document context string
        """
        try:
            # Search documents with fallback to global documents
            search_user_id = user_id or "global_admin"
            
            relevant_docs = await self.document_service.search_documents(
                query=query,
                user_id=search_user_id,
                limit=3,
                similarity_threshold=0.3
            )
            
            if not relevant_docs:
                return ""
            
            doc_parts = []
            doc_parts.append("Relevant information from coffee farming documents:")
            
            for i, doc in enumerate(relevant_docs, 1):
                content = doc.get("content", "")
                filename = doc.get("filename", "")
                similarity = doc.get("similarity_score", 0)
                
                if content and similarity > 0.3:
                    doc_parts.append(f"{i}. From '{filename}': {content[:500]}...")
            
            return "\n".join(doc_parts) if len(doc_parts) > 1 else ""
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return ""
    
    async def _get_weather_context(self, context: Optional[Dict[str, Any]], message: str) -> str:
        """
        Get weather context if relevant to the user's question and location is available.
        
        Args:
            context: User context that might contain location
            message: User's message to check if weather-related
            
        Returns:
            Formatted weather context string
        """
        try:
            # Check if the message is weather-related
            weather_keywords = [
                "weather", "rain", "dry", "wet", "season", "temperature", "humidity",
                "drought", "flooding", "planting", "harvest", "spray", "irrigation",
                "when to", "timing", "climate", "wind", "sunshine"
            ]
            
            message_lower = message.lower()
            is_weather_related = any(keyword in message_lower for keyword in weather_keywords)
            
            if not is_weather_related:
                return ""
            
            # Default to common Kenya coffee regions if no specific location
            # Nyeri coordinates (major coffee region)
            latitude = -0.4167
            longitude = 36.95
            
            # Try to get location from context if available
            if context:
                user_location = context.get("location") or context.get("farm_location")
                if user_location:
                    # Parse coordinates if provided (future enhancement)
                    pass
            
            # Get current weather and short forecast
            current_weather = await self.weather_service.get_current_weather(latitude, longitude)
            forecast = await self.weather_service.get_forecast(latitude, longitude, days=3)
            
            if not current_weather:
                return ""
            
            weather_parts = []
            weather_parts.append("Current weather conditions for your farming area:")
            weather_parts.append(f"• Temperature: {current_weather.temperature:.1f}°C")
            weather_parts.append(f"• Humidity: {current_weather.humidity:.0f}%")
            weather_parts.append(f"• Condition: {current_weather.condition}")
            
            if current_weather.precipitation > 0:
                weather_parts.append(f"• Current rainfall: {current_weather.precipitation:.1f}mm")
            
            if forecast:
                weather_parts.append(f"\nNext 3 days outlook:")
                for day in forecast[:3]:
                    weather_parts.append(
                        f"• {day.date}: {day.temperature_min:.0f}-{day.temperature_max:.0f}°C, "
                        f"{day.precipitation:.1f}mm rain ({day.precipitation_probability:.0f}% chance)"
                    )
            
            return "\n".join(weather_parts)
            
        except Exception as e:
            logger.error(f"Error getting weather context: {str(e)}")
            return ""
    
    async def health_check(self) -> Dict[str, str]:
        """
        Perform health check on agent dependencies.
        
        Returns:
            Dictionary with dependency status
        """
        dependencies = {}
        
        # Check Cerebras API
        try:
            cerebras_healthy = await self.llm_client.health_check()
            dependencies["cerebras_api"] = "connected" if cerebras_healthy else "disconnected"
        except Exception as e:
            logger.error(f"Cerebras health check error: {str(e)}")
            dependencies["cerebras_api"] = "error"
        
        # Check Django backend (placeholder for Phase 3)
        dependencies["django_backend"] = "not_configured"
        
        return dependencies


# Global service instance
agent_service = AgentService()