"""
Database configuration and connection management.
Handles PostgreSQL, Qdrant, and Redis connections.
"""

import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import redis.asyncio as redis
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self):
        self.postgres_engine = None
        self.postgres_session_factory = None
        self.qdrant_client = None
        self.redis_client = None
        
    async def initialize(self):
        """Initialize all database connections."""
        await self._init_postgres()
        await self._init_qdrant()
        await self._init_redis()
        
    async def _init_postgres(self):
        """Initialize PostgreSQL connection."""
        try:
            postgres_url = (
                f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
                f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
            )
            
            self.postgres_engine = create_async_engine(
                postgres_url,
                echo=settings.debug,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            
            self.postgres_session_factory = async_sessionmaker(
                self.postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("PostgreSQL connection initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    
    async def _init_qdrant(self):
        """Initialize Qdrant vector database."""
        try:
            self.qdrant_client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                timeout=30
            )
            
            # Create collections if they don't exist
            await self._create_qdrant_collections()
            
            logger.info("Qdrant connection initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            raise
    
    async def _init_redis(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            
            logger.info("Redis connection initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    async def _create_qdrant_collections(self):
        """Create Qdrant collections for different types of embeddings."""
        collections = [
            {
                "name": "conversation_embeddings",
                "vector_size": 384,  # sentence-transformers/all-MiniLM-L6-v2
                "distance": Distance.COSINE
            },
            {
                "name": "user_context_embeddings", 
                "vector_size": 384,
                "distance": Distance.COSINE
            }
        ]
        
        for collection in collections:
            try:
                # Check if collection exists
                collections_info = self.qdrant_client.get_collections()
                existing_names = [col.name for col in collections_info.collections]
                
                if collection["name"] not in existing_names:
                    self.qdrant_client.create_collection(
                        collection_name=collection["name"],
                        vectors_config=VectorParams(
                            size=collection["vector_size"],
                            distance=collection["distance"]
                        )
                    )
                    logger.info(f"Created Qdrant collection: {collection['name']}")
                else:
                    logger.info(f"Qdrant collection already exists: {collection['name']}")
                    
            except Exception as e:
                logger.error(f"Failed to create collection {collection['name']}: {e}")
                raise
    
    async def get_postgres_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get PostgreSQL session."""
        if not self.postgres_session_factory:
            raise RuntimeError("PostgreSQL not initialized")
            
        async with self.postgres_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_qdrant_client(self) -> QdrantClient:
        """Get Qdrant client."""
        if not self.qdrant_client:
            raise RuntimeError("Qdrant not initialized")
        return self.qdrant_client
    
    def get_redis_client(self):
        """Get Redis client."""
        if not self.redis_client:
            raise RuntimeError("Redis not initialized")
        return self.redis_client
    
    async def health_check(self) -> dict:
        """Check health of all database connections."""
        health = {}
        
        # PostgreSQL health
        try:
            async with self.postgres_session_factory() as session:
                await session.execute("SELECT 1")
            health["postgres"] = "connected"
        except Exception as e:
            health["postgres"] = f"error: {str(e)}"
        
        # Qdrant health
        try:
            self.qdrant_client.get_collections()
            health["qdrant"] = "connected"
        except Exception as e:
            health["qdrant"] = f"error: {str(e)}"
        
        # Redis health
        try:
            await self.redis_client.ping()
            health["redis"] = "connected"
        except Exception as e:
            health["redis"] = f"error: {str(e)}"
        
        return health
    
    async def close(self):
        """Close all database connections."""
        if self.postgres_engine:
            await self.postgres_engine.dispose()
        
        if self.qdrant_client:
            self.qdrant_client.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("All database connections closed")


# Global database manager instance
db_manager = DatabaseManager()