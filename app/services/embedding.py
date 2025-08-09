"""
Vector embedding service for semantic memory search.
Handles text embeddings and vector database operations.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
import numpy as np

from app.database import db_manager

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for creating and managing text embeddings."""
    
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self.embedding_model = None
        self.vector_size = 384
        
    async def initialize(self):
        """Initialize the embedding model."""
        try:
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model {self.model_name} initialized")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding vector for text."""
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")
        
        try:
            # Clean and prepare text
            cleaned_text = self._clean_text(text)
            
            # Generate embedding
            embedding = self.embedding_model.encode(cleaned_text)
            
            # Convert to list for JSON serialization
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            raise
    
    def create_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts."""
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")
        
        try:
            # Clean texts
            cleaned_texts = [self._clean_text(text) for text in texts]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(cleaned_texts)
            
            # Convert to list of lists
            return [embedding.tolist() for embedding in embeddings]
            
        except Exception as e:
            logger.error(f"Failed to create batch embeddings: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean and prepare text for embedding."""
        if not text:
            return ""
        
        # Basic text cleaning
        cleaned = text.strip()
        
        # Remove excessive whitespace
        cleaned = " ".join(cleaned.split())
        
        # Truncate if too long (model limit is usually 512 tokens)
        if len(cleaned) > 2000:  # Conservative limit
            cleaned = cleaned[:2000] + "..."
        
        return cleaned
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0


class VectorMemoryService:
    """Service for managing vector memory in Qdrant."""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.conversation_collection = "conversation_embeddings"
        self.context_collection = "user_context_embeddings"
    
    async def initialize(self):
        """Initialize the vector memory service."""
        await self.embedding_service.initialize()
        logger.info("Vector memory service initialized")
    
    async def store_conversation_memory(
        self,
        message_id: str,
        user_id: str,
        session_id: str,
        content: str,
        message_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store conversation message in vector database."""
        try:
            # Create embedding
            embedding = self.embedding_service.create_embedding(content)
            
            # Generate unique point ID
            point_id = str(uuid.uuid4())
            
            # Prepare metadata
            point_metadata = {
                "message_id": message_id,
                "user_id": user_id,
                "session_id": session_id,
                "message_type": message_type,
                "content": content[:500],  # Store truncated content for search
                "timestamp": metadata.get("timestamp") if metadata else None,
                **(metadata or {})
            }
            
            # Create point
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=point_metadata
            )
            
            # Store in Qdrant
            qdrant_client = db_manager.get_qdrant_client()
            qdrant_client.upsert(
                collection_name=self.conversation_collection,
                points=[point]
            )
            
            logger.info(f"Stored conversation memory for message {message_id}")
            return point_id
            
        except Exception as e:
            logger.error(f"Failed to store conversation memory: {e}")
            raise
    
    async def search_similar_conversations(
        self,
        query_text: str,
        user_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar conversations in memory."""
        try:
            # Create query embedding
            query_embedding = self.embedding_service.create_embedding(query_text)
            
            # Create filter for user
            user_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            )
            
            # Search in Qdrant
            qdrant_client = db_manager.get_qdrant_client()
            search_results = qdrant_client.search(
                collection_name=self.conversation_collection,
                query_vector=query_embedding,
                query_filter=user_filter,
                limit=limit,
                score_threshold=similarity_threshold
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "message_id": result.payload.get("message_id"),
                    "content": result.payload.get("content"),
                    "message_type": result.payload.get("message_type"),
                    "session_id": result.payload.get("session_id"),
                    "similarity_score": result.score,
                    "timestamp": result.payload.get("timestamp"),
                    "metadata": {k: v for k, v in result.payload.items() 
                               if k not in ["message_id", "content", "message_type", "session_id", "user_id"]}
                })
            
            logger.info(f"Found {len(results)} similar conversations for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search similar conversations: {e}")
            return []
    
    async def store_user_context(
        self,
        user_id: str,
        context_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store user context information."""
        try:
            # Create embedding
            embedding = self.embedding_service.create_embedding(content)
            
            # Generate unique point ID
            point_id = str(uuid.uuid4())
            
            # Prepare metadata
            point_metadata = {
                "user_id": user_id,
                "context_type": context_type,
                "content": content[:500],
                **(metadata or {})
            }
            
            # Create point
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=point_metadata
            )
            
            # Store in Qdrant
            qdrant_client = db_manager.get_qdrant_client()
            qdrant_client.upsert(
                collection_name=self.context_collection,
                points=[point]
            )
            
            logger.info(f"Stored user context for user {user_id}")
            return point_id
            
        except Exception as e:
            logger.error(f"Failed to store user context: {e}")
            raise
    
    async def get_user_context(
        self,
        user_id: str,
        context_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve user context information."""
        try:
            # Create filter
            filter_conditions = [
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            ]
            
            if context_types:
                for context_type in context_types:
                    filter_conditions.append(
                        FieldCondition(
                            key="context_type",
                            match=MatchValue(value=context_type)
                        )
                    )
            
            user_filter = Filter(must=filter_conditions)
            
            # Search in Qdrant
            qdrant_client = db_manager.get_qdrant_client()
            
            # Use scroll to get all matching points
            results, _ = qdrant_client.scroll(
                collection_name=self.context_collection,
                scroll_filter=user_filter,
                limit=limit
            )
            
            # Format results
            context_data = []
            for result in results:
                context_data.append({
                    "context_type": result.payload.get("context_type"),
                    "content": result.payload.get("content"),
                    "metadata": {k: v for k, v in result.payload.items() 
                               if k not in ["user_id", "context_type", "content"]}
                })
            
            logger.info(f"Retrieved {len(context_data)} context items for user {user_id}")
            return context_data
            
        except Exception as e:
            logger.error(f"Failed to get user context: {e}")
            return []


# Global service instances
embedding_service = EmbeddingService()
vector_memory_service = VectorMemoryService()