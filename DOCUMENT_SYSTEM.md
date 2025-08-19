# 📄 Document System & RAG Integration

## Overview

The Guka AI Agent now supports **Phase 4: Document Intelligence** with RAG (Retrieval Augmented Generation) capabilities! This allows farmers and administrators to upload coffee farming documents that the AI agent can reference when answering questions.

## 🚀 Features

### Document Upload & Processing
- **Multi-format support**: PDF, DOCX, TXT files
- **Automatic text extraction** with intelligent chunking
- **Vector embeddings** for semantic search
- **Metadata management** with tags and descriptions
- **User-specific documents** with privacy controls

### RAG-Enhanced Chat
- **Automatic document search** when relevant to user questions
- **Context-aware responses** using uploaded knowledge
- **Fallback to general knowledge** when no specific documents found
- **Seamless integration** with existing memory system

### Document Management
- **List all documents** with metadata
- **Search documents** by content similarity
- **Delete documents** with proper cleanup
- **User permissions** for document access

## 📡 API Endpoints

### Document Upload
```bash
POST /documents/upload

# Form data:
# - file: The document file (PDF/DOCX/TXT)
# - user_id: User identifier
# - description: Optional description
# - tags: Optional comma-separated tags
```

### Document Search
```bash
POST /documents/search

# JSON body:
{
  "query": "coffee leaf rust treatment",
  "user_id": "farmer_123",  # optional
  "limit": 5,
  "similarity_threshold": 0.7,
  "tags": ["coffee", "disease"]  # optional
}
```

### List Documents
```bash
GET /documents?user_id=farmer_123&limit=20&offset=0
```

### Get Document Info
```bash
GET /documents/{document_id}?user_id=farmer_123
```

### Delete Document
```bash
DELETE /documents/{document_id}?user_id=farmer_123
```

## 💡 Usage Examples

### 1. Upload a Coffee Farming Guide

**PowerShell:**
```powershell
$form = @{
    file = Get-Item "coffee_farming_guide.pdf"
    user_id = "farmer_123"
    description = "Complete guide to coffee farming in Kenya"
    tags = "coffee,farming,kenya,guide"
}

Invoke-RestMethod -Uri "http://localhost:8001/documents/upload" -Method Post -Form $form
```

**cURL:**
```bash
curl -X POST http://localhost:8001/documents/upload \
  -F "file=@coffee_farming_guide.pdf" \
  -F "user_id=farmer_123" \
  -F "description=Complete guide to coffee farming" \
  -F "tags=coffee,farming,guide"
```

### 2. Search Documents
```bash
curl -X POST http://localhost:8001/documents/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to treat coffee berry disease?",
    "limit": 3,
    "similarity_threshold": 0.75
  }'
```

### 3. RAG-Enhanced Chat
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My coffee plants have dark spots on berries, what should I do?",
    "user_id": "farmer_123",
    "session_id": "session_456"
  }'
```

The chat endpoint will automatically:
1. Search user's uploaded documents for relevant information
2. Fall back to general document knowledge if needed  
3. Provide the AI with context from relevant documents
4. Generate a comprehensive, knowledge-enhanced response

## 🧪 Testing

### Run Document System Tests
```bash
# Make sure you're in the guka-ai-agent directory
cd guka-ai-agent

# Run the test script
python test_documents.py
```

This will:
1. Upload the test coffee farming document
2. Test document search with various queries
3. Demonstrate RAG integration
4. List all uploaded documents

### Test with Real Documents

1. **Prepare your coffee farming documents** (PDF, DOCX, or TXT)
2. **Upload using the API endpoints** shown above
3. **Ask the AI agent questions** related to your documents
4. **See RAG in action** as it references your uploaded knowledge

## 📊 System Architecture

```
User Question → Document Search → Vector Similarity → Top Results
     ↓              ↓                    ↓              ↓
Chat Endpoint → RAG Context → Enhanced Prompt → AI Response
```

### Document Processing Flow
```
File Upload → Text Extraction → Chunking → Embeddings → Vector Storage
     ↓              ↓             ↓          ↓            ↓
   PDF/DOCX      Plain Text   1000-char   384-dim     Qdrant DB
                               chunks     vectors      + Metadata
```

### RAG Integration
```
User Question → Semantic Search → Relevant Chunks → Context Assembly
     ↓               ↓                ↓                 ↓
Enhanced Chat Context → LLM Processing → Knowledge-Rich Response
```

## 🔧 Configuration

The document system uses the existing vector database configuration:

```python
# In app/config.py
qdrant_host: str = "localhost"
qdrant_port: int = 6333
```

Documents are stored in:
- **Vector Database**: Qdrant (for semantic search)
- **Metadata Database**: PostgreSQL (for document info)
- **File Storage**: Local filesystem (uploads/ directory)

## 🛡️ Security & Permissions

### User Isolation
- Users can only access their own uploaded documents by default
- Global documents (user_id = None) are accessible to all users
- API endpoints respect user permissions

### File Validation
- Supported formats: PDF, DOCX, TXT
- File size limits (configurable)
- Content extraction with error handling

### Data Privacy
- Document chunks stored with user metadata
- Search results filtered by user permissions
- Secure file cleanup on deletion

## 📈 Performance & Scalability

### Vector Search Optimization
- **384-dimensional embeddings** using `sentence-transformers/all-MiniLM-L6-v2`
- **Cosine similarity** for semantic matching
- **Threshold-based filtering** (default: 0.75 for high relevance)

### Chunking Strategy
- **Smart sentence-based chunking** with overlap
- **1000 characters per chunk** with 200-character overlap
- **Preserves context** across chunk boundaries

### Caching & Performance
- **Embedding model caching** for faster processing
- **Batch processing** for multiple documents
- **Async operations** for scalable performance

## 🐛 Troubleshooting

### Common Issues

1. **Document Upload Fails**
   - Check file format (PDF/DOCX/TXT only)
   - Verify file is not corrupted
   - Ensure sufficient disk space

2. **No Search Results Found**
   - Lower similarity_threshold (try 0.6-0.7)
   - Try different search terms
   - Check if documents were uploaded successfully

3. **RAG Not Working in Chat**
   - Verify documents contain relevant content
   - Test document search directly first
   - Check vector database connectivity

### Debug Mode
Set `DEBUG=true` in `.env` for detailed logging:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🔮 Future Enhancements

- **Advanced document types**: Excel, PowerPoint support
- **OCR integration**: Scanned document processing  
- **Document versioning**: Track document updates
- **Advanced chunking**: Context-aware splitting
- **Multi-language support**: Swahili document processing
- **Document analytics**: Usage tracking and insights

## 📞 Support

For issues with the document system:

1. Check the logs for detailed error messages
2. Verify all dependencies are installed
3. Test with the provided test documents first
4. Check database connectivity (PostgreSQL + Qdrant)

---

🌱 **Ready to enhance your coffee farming knowledge with AI!** Upload your documents and experience the power of RAG-enhanced conversations.
