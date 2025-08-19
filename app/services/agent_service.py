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
        self.document_service = document_service
        
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
            
            # Build enhanced context with memory and documents
            memory_context = self._build_memory_context(relevant_memories)
            
            # Build messages for LLM with memory and document context
            messages = AgentPrompts.build_messages(
                user_message=request.message,
                context=request.context,
                memory_context=memory_context,
                document_context=document_context
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