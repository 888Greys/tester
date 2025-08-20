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
from app.services.memory_intelligence import memory_intelligence_service

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
            
            # Get intelligent memory context instead of basic memory (only if user_id provided)
            if request.user_id:
                intelligent_context = await memory_intelligence_service.get_intelligent_memory_context(
                    query=request.message,
                    user_id=request.user_id,
                    max_memories=5,
                    include_insights=True
                )
                
                # Extract relevant memories and insights
                relevant_memories = intelligent_context.get("relevant_memories", [])
                memory_insights = intelligent_context.get("memory_insights", [])
                context_summary = intelligent_context.get("context_summary", "")
                
                # Build enhanced context with memory intelligence
                enhanced_memory_context = self._build_intelligent_memory_context(
                    relevant_memories, memory_insights, context_summary
                )
            else:
                # Fallback to basic memory context for non-authenticated users
                relevant_memories = request.context.get("relevant_memories", []) if request.context else []
                enhanced_memory_context = self._build_memory_context(relevant_memories)
            
            # Search relevant documents for the user's question
            document_context = await self._search_relevant_documents(request.message, request.user_id)
            
            # Get weather context if user has location data
            weather_context = await self._get_weather_context(request.context, request.message)
            
            # Get conversation history for this session to maintain context continuity
            conversation_history = []
            if request.user_id:
                from app.services.memory import memory_service
                conversation_history = await memory_service.get_conversation_history(
                    session_id=session_id,
                    limit=10  # Get last 10 messages for context
                )
            
            # Build messages for LLM with conversation history, memory, document, and weather context
            messages = AgentPrompts.build_messages_with_history(
                user_message=request.message,
                conversation_history=conversation_history,
                context=request.context,
                memory_context=enhanced_memory_context,
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
    
    def _build_intelligent_memory_context(
        self, 
        relevant_memories: list, 
        memory_insights: list, 
        context_summary: str
    ) -> str:
        """
        Build enhanced memory context with intelligence insights.
        
        Args:
            relevant_memories: List of enhanced memory items
            memory_insights: List of memory insights
            context_summary: Summary of the context
            
        Returns:
            Enhanced memory context string
        """
        if not relevant_memories and not memory_insights:
            return ""
        
        context_parts = []
        
        # Add context summary if available
        if context_summary:
            context_parts.append(f"Context: {context_summary}")
        
        # Add relevant memories with enhanced information
        if relevant_memories:
            context_parts.append("Recent relevant conversations:")
            for i, memory in enumerate(relevant_memories[:3], 1):
                content = memory.get("content", "")
                enhanced_relevance = memory.get("enhanced_relevance", 0)
                memory_type = memory.get("memory_type", "general")
                
                if content and enhanced_relevance > 0.6:
                    relevance_desc = "High" if enhanced_relevance > 0.8 else "Medium"
                    context_parts.append(
                        f"{i}. [{memory_type.title()}] {content} "
                        f"(relevance: {relevance_desc})"
                    )
        
        # Add key insights
        if memory_insights:
            context_parts.append("Key farming insights from your history:")
            for insight in memory_insights[:2]:
                context_parts.append(f"• {insight.topic}: {insight.summary}")
        
        return "\n".join(context_parts)
    
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