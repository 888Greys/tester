"""
Document processing service for handling coffee farming documents.
Supports PDF, DOCX, TXT files and integrates with the existing vector database.
"""

import logging
import uuid
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import aiofiles

import pdfplumber
from docx import Document as DocxDocument
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.database import db_manager
from app.services.embedding import vector_memory_service
from app.config import settings

logger = logging.getLogger(__name__)


class DocumentChunk:
    """Represents a chunk of a document."""
    
    def __init__(
        self,
        content: str,
        document_id: str,
        chunk_index: int,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.start_page = start_page
        self.end_page = end_page
        self.metadata = metadata or {}
        self.chunk_id = f"{document_id}_chunk_{chunk_index}"


class DocumentProcessor:
    """Handles document parsing and text extraction."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_file(
        self, 
        file_content: bytes, 
        filename: str,
        file_type: str
    ) -> List[str]:
        """Process a file and extract text content."""
        
        try:
            if file_type.startswith('text/'):
                return await self._process_text_file(file_content)
            elif file_type == 'application/pdf':
                return await self._process_pdf_file(file_content)
            elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
                return await self._process_docx_file(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            raise
    
    async def _process_text_file(self, file_content: bytes) -> List[str]:
        """Process plain text files."""
        text = file_content.decode('utf-8', errors='ignore')
        return self._chunk_text(text)
    
    async def _process_pdf_file(self, file_content: bytes) -> List[str]:
        """Process PDF files."""
        loop = asyncio.get_event_loop()
        
        def extract_pdf_text():
            import io
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                text_pages = []
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    text_pages.append(page_text)
                return "\n\n".join(text_pages)
        
        text = await loop.run_in_executor(self.executor, extract_pdf_text)
        return self._chunk_text(text)
    
    async def _process_docx_file(self, file_content: bytes) -> List[str]:
        """Process DOCX files."""
        loop = asyncio.get_event_loop()
        
        def extract_docx_text():
            import io
            doc = DocxDocument(io.BytesIO(file_content))
            paragraphs = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text.strip())
            return "\n\n".join(paragraphs)
        
        text = await loop.run_in_executor(self.executor, extract_docx_text)
        return self._chunk_text(text)
    
    def _chunk_text(self, text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        if not text.strip():
            return []
        
        # Split by sentences first for better chunks
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed max size, start new chunk
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Create overlap by keeping last part of previous chunk
                if overlap > 0 and len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:] + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += (". " if current_chunk else "") + sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # If no sentences found, split by characters
        if not chunks and text:
            chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
        
        return chunks


class DocumentService:
    """Main service for document management and storage."""
    
    def __init__(self):
        self.processor = DocumentProcessor()
        self.document_collection = "document_embeddings"
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
    
    async def initialize(self):
        """Initialize the document service."""
        await self._create_document_collection()
        logger.info("Document service initialized")
    
    async def _create_document_collection(self):
        """Create document collection in Qdrant if it doesn't exist."""
        try:
            qdrant_client = db_manager.get_qdrant_client()
            collections_info = qdrant_client.get_collections()
            existing_names = [col.name for col in collections_info.collections]
            
            if self.document_collection not in existing_names:
                from qdrant_client.models import Distance, VectorParams
                
                qdrant_client.create_collection(
                    collection_name=self.document_collection,
                    vectors_config=VectorParams(
                        size=384,  # sentence-transformers/all-MiniLM-L6-v2
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created document collection: {self.document_collection}")
            else:
                logger.info(f"Document collection already exists: {self.document_collection}")
                
        except Exception as e:
            logger.error(f"Failed to create document collection: {e}")
            raise
    
    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Upload and process a document."""
        
        try:
            # Validate file
            file_type = self._get_file_type(filename)
            if not self._is_supported_file_type(file_type):
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Create file hash for deduplication
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Save file to disk
            file_path = self.upload_dir / f"{document_id}_{filename}"
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Process document and extract text
            text_chunks = await self.processor.process_file(
                file_content, filename, file_type
            )
            
            if not text_chunks:
                raise ValueError("No text content could be extracted from the document")
            
            # Store document metadata in PostgreSQL
            await self._store_document_metadata(
                document_id=document_id,
                filename=filename,
                file_path=str(file_path),
                file_hash=file_hash,
                file_size=len(file_content),
                file_type=file_type,
                user_id=user_id,
                description=description,
                tags=tags,
                chunk_count=len(text_chunks)
            )
            
            # Create embeddings and store in vector database
            await self._store_document_chunks(
                document_id=document_id,
                text_chunks=text_chunks,
                filename=filename,
                user_id=user_id,
                file_type=file_type
            )
            
            logger.info(f"Document {filename} uploaded successfully with ID: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to upload document {filename}: {e}")
            # Clean up file if it was saved
            if 'file_path' in locals() and Path(file_path).exists():
                Path(file_path).unlink(missing_ok=True)
            raise
    
    async def search_documents(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5,
        similarity_threshold: float = 0.3,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search documents using semantic similarity."""
        
        try:
            # Create query embedding
            embedding = vector_memory_service.embedding_service.create_embedding(query)
            
            # Create filter
            from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
            
            filter_conditions = []
            if user_id:
                filter_conditions.append(
                    FieldCondition(key="user_id", match=MatchValue(value=user_id))
                )
            if tags:
                filter_conditions.append(
                    FieldCondition(key="tags", match=MatchAny(any=tags))
                )
            
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Search in Qdrant
            qdrant_client = db_manager.get_qdrant_client()
            search_results = qdrant_client.search(
                collection_name=self.document_collection,
                query_vector=embedding,
                query_filter=search_filter,
                limit=limit,
                score_threshold=similarity_threshold
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    "chunk_id": result.payload.get("chunk_id"),
                    "document_id": result.payload.get("document_id"),
                    "filename": result.payload.get("filename"),
                    "content": result.payload.get("content"),
                    "chunk_index": result.payload.get("chunk_index"),
                    "similarity_score": result.score,
                    "metadata": {
                        k: v for k, v in result.payload.items()
                        if k not in ["chunk_id", "document_id", "content", "user_id"]
                    }
                })
            
            logger.info(f"Found {len(results)} relevant document chunks for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            return []
    
    async def get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata."""
        try:
            async with db_manager.get_postgres_session() as session:
                from sqlalchemy import text
                
                query = text("""
                    SELECT 
                        document_id, filename, file_size, file_type, 
                        description, tags, chunk_count, upload_date,
                        user_id
                    FROM documents 
                    WHERE document_id = :document_id
                """)
                
                result = await session.execute(query, {"document_id": document_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "document_id": row.document_id,
                        "filename": row.filename,
                        "file_size": row.file_size,
                        "file_type": row.file_type,
                        "description": row.description,
                        "tags": row.tags,
                        "chunk_count": row.chunk_count,
                        "upload_date": row.upload_date.isoformat(),
                        "user_id": row.user_id
                    }
                return None
                
        except Exception as e:
            logger.error(f"Failed to get document info: {e}")
            return None
    
    async def list_documents(
        self, 
        user_id: Optional[str] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List uploaded documents."""
        try:
            async with db_manager.get_postgres_session() as session:
                from sqlalchemy import text
                
                query = text("""
                    SELECT 
                        document_id, filename, file_size, file_type, 
                        description, tags, chunk_count, upload_date,
                        user_id
                    FROM documents 
                    WHERE (:user_id IS NULL OR user_id = :user_id)
                    ORDER BY upload_date DESC
                    LIMIT :limit OFFSET :offset
                """)
                
                result = await session.execute(query, {
                    "user_id": user_id,
                    "limit": limit,
                    "offset": offset
                })
                
                documents = []
                for row in result.fetchall():
                    documents.append({
                        "document_id": row.document_id,
                        "filename": row.filename,
                        "file_size": row.file_size,
                        "file_type": row.file_type,
                        "description": row.description,
                        "tags": row.tags,
                        "chunk_count": row.chunk_count,
                        "upload_date": row.upload_date.isoformat(),
                        "user_id": row.user_id
                    })
                
                return documents
                
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []
    
    async def delete_document(self, document_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a document and its embeddings."""
        try:
            # Get document info first
            doc_info = await self.get_document_info(document_id)
            if not doc_info:
                return False
            
            # Check user permission if user_id provided
            if user_id and doc_info.get("user_id") != user_id:
                return False
            
            # Delete from vector database
            qdrant_client = db_manager.get_qdrant_client()
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            delete_filter = Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            )
            
            qdrant_client.delete(
                collection_name=self.document_collection,
                points_selector=delete_filter
            )
            
            # Delete from PostgreSQL
            async with db_manager.get_postgres_session() as session:
                from sqlalchemy import text
                
                query = text("DELETE FROM documents WHERE document_id = :document_id")
                await session.execute(query, {"document_id": document_id})
                await session.commit()
            
            # Delete file from disk
            if "file_path" in doc_info:
                file_path = Path(doc_info["file_path"])
                if file_path.exists():
                    file_path.unlink(missing_ok=True)
            
            logger.info(f"Document {document_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def _store_document_metadata(
        self,
        document_id: str,
        filename: str,
        file_path: str,
        file_hash: str,
        file_size: int,
        file_type: str,
        user_id: str,
        description: Optional[str],
        tags: Optional[List[str]],
        chunk_count: int
    ):
        """Store document metadata in PostgreSQL."""
        async with db_manager.get_postgres_session() as session:
            from sqlalchemy import text
            
            # First, ensure the documents table exists
            create_table_query = text("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    document_id VARCHAR(36) UNIQUE NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_hash VARCHAR(64) NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type VARCHAR(100) NOT NULL,
                    user_id VARCHAR(100) NOT NULL,
                    description TEXT,
                    tags TEXT[],
                    chunk_count INTEGER DEFAULT 0,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await session.execute(create_table_query)
            
            # Insert document metadata
            insert_query = text("""
                INSERT INTO documents (
                    document_id, filename, file_path, file_hash, file_size, 
                    file_type, user_id, description, tags, chunk_count
                ) VALUES (
                    :document_id, :filename, :file_path, :file_hash, :file_size,
                    :file_type, :user_id, :description, :tags, :chunk_count
                )
            """)
            
            await session.execute(insert_query, {
                "document_id": document_id,
                "filename": filename,
                "file_path": file_path,
                "file_hash": file_hash,
                "file_size": file_size,
                "file_type": file_type,
                "user_id": user_id,
                "description": description,
                "tags": tags,
                "chunk_count": chunk_count
            })
            
            await session.commit()
    
    async def _store_document_chunks(
        self,
        document_id: str,
        text_chunks: List[str],
        filename: str,
        user_id: str,
        file_type: str
    ):
        """Store document chunks as embeddings in vector database."""
        
        # Create embeddings for all chunks
        embeddings = vector_memory_service.embedding_service.create_batch_embeddings(text_chunks)
        
        # Create points for Qdrant
        from qdrant_client.models import PointStruct
        points = []
        
        for i, (chunk_text, embedding) in enumerate(zip(text_chunks, embeddings)):
            point_id = str(uuid.uuid4())
            
            metadata = {
                "document_id": document_id,
                "chunk_id": f"{document_id}_chunk_{i}",
                "chunk_index": i,
                "filename": filename,
                "file_type": file_type,
                "user_id": user_id,
                "content": chunk_text[:500],  # Store truncated content for search
                "full_content": chunk_text,  # Store full content
                "upload_date": datetime.utcnow().isoformat(),
                "tags": ["coffee", "farming"],  # Default tags
            }
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=metadata
            )
            points.append(point)
        
        # Store in Qdrant
        qdrant_client = db_manager.get_qdrant_client()
        qdrant_client.upsert(
            collection_name=self.document_collection,
            points=points
        )
        
        logger.info(f"Stored {len(points)} document chunks for {filename}")
    
    def _get_file_type(self, filename: str) -> str:
        """Get MIME type from filename."""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def _is_supported_file_type(self, file_type: str) -> bool:
        """Check if file type is supported."""
        supported_types = [
            'text/plain',
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ]
        return file_type in supported_types


# Global service instance
document_service = DocumentService()
