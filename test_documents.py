#!/usr/bin/env python3
"""
Test script to demonstrate document upload and RAG functionality.
Run this script to test the document upload and search features.
"""

import asyncio
import json
import logging
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_document_system():
    """Test the document upload and search system."""
    
    # Import required modules
    from app.services.document_service import document_service
    from app.services.embedding import vector_memory_service
    from app.database import db_manager
    
    try:
        # Initialize services
        logger.info("Initializing services...")
        await db_manager.initialize()
        await vector_memory_service.initialize()
        await document_service.initialize()
        
        # Test document upload
        logger.info("Testing document upload...")
        
        # Read test document
        test_file = Path("test_coffee_document.txt")
        if test_file.exists():
            with open(test_file, 'rb') as f:
                file_content = f.read()
            
            # Upload document
            document_id = await document_service.upload_document(
                file_content=file_content,
                filename="coffee_farming_guide.txt",
                user_id="test_farmer",
                description="Comprehensive guide to coffee farming best practices",
                tags=["coffee", "farming", "guide", "kenya"]
            )
            
            logger.info(f"Document uploaded successfully with ID: {document_id}")
            
            # Test document search
            logger.info("Testing document search...")
            
            test_queries = [
                "How to treat coffee leaf rust?",
                "What varieties of coffee are grown in Kenya?",
                "When is the best time to harvest coffee?",
                "How to manage coffee berry disease?"
            ]
            
            for query in test_queries:
                logger.info(f"\nSearching for: '{query}'")
                
                results = await document_service.search_documents(
                    query=query,
                    limit=3,
                    similarity_threshold=0.7
                )
                
                if results:
                    for result in results:
                        logger.info(f"Found relevant content (score: {result['similarity_score']:.3f}):")
                        logger.info(f"Content: {result['content'][:200]}...")
                else:
                    logger.info("No relevant documents found")
            
            # Test document listing
            logger.info("\nTesting document listing...")
            documents = await document_service.list_documents(limit=10)
            
            logger.info(f"Found {len(documents)} documents in the system:")
            for doc in documents:
                logger.info(f"- {doc['filename']} (chunks: {doc['chunk_count']})")
            
            logger.info("\nDocument system test completed successfully!")
            
        else:
            logger.error("Test document file not found. Please ensure 'test_coffee_document.txt' exists.")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        # Clean up
        await db_manager.close()


async def test_rag_chat():
    """Test RAG-enhanced chat functionality."""
    
    # This would require the full chat system to be running
    # For now, we'll just demonstrate the document search component
    
    from app.services.document_service import document_service
    
    logger.info("Testing RAG chat integration...")
    
    # Simulate a farming question
    farmer_question = "My coffee plants have orange spots on the leaves. What should I do?"
    
    # Search for relevant documents
    relevant_docs = await document_service.search_documents(
        query=farmer_question,
        limit=3,
        similarity_threshold=0.7
    )
    
    if relevant_docs:
        logger.info("RAG Context Found:")
        for doc in relevant_docs:
            logger.info(f"- Similarity: {doc['similarity_score']:.3f}")
            logger.info(f"- Content: {doc['full_content'][:300]}...")
            
        logger.info("This context would be provided to the LLM for generating a comprehensive answer.")
    else:
        logger.info("No relevant documents found for RAG enhancement.")


def run_tests():
    """Run the document system tests."""
    
    logger.info("=== Guka AI Agent - Document System Tests ===")
    
    # Run tests
    asyncio.run(test_document_system())
    
    logger.info("\n=== RAG Chat Integration Test ===")
    asyncio.run(test_rag_chat())
    
    logger.info("\n=== All Tests Completed ===")


if __name__ == "__main__":
    run_tests()
