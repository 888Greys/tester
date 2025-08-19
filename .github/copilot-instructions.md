# Guka AI Agent - AI Coding Assistant Instructions

## Architecture Overview

This is a **production-ready FastAPI service** designed as an AI farming assistant for Kenyan coffee farmers. The system uses a multi-database architecture with vector embeddings for memory and document intelligence.

**Core Components:**
- `app/api.py` - FastAPI routes with startup/shutdown lifecycle management
- `app/services/` - Business logic layer (agent, memory, document processing)
- `app/models/` - Pydantic models and SQLAlchemy ORM definitions
- `app/database.py` - Multi-database manager (PostgreSQL, Qdrant, Redis)

## Key Development Patterns

### Service Layer Architecture
Services follow dependency injection pattern with health checks:
```python
# All services implement initialize() and health_check() methods
await db_manager.initialize()
await vector_memory_service.initialize()
```

### Memory System Design
- **PostgreSQL**: Structured data (user profiles, conversations)
- **Qdrant**: Vector embeddings for semantic search
- **Redis**: Session caching and temporary data
- Memory operations in `app/services/memory.py` use async SQLAlchemy with vector search

### Document Intelligence (RAG)
- Document processing in `app/services/document_service.py`
- Supports PDF, DOCX, TXT with intelligent chunking
- Vector embeddings stored in Qdrant for semantic retrieval
- RAG responses integrated in chat endpoint

## Critical Workflows

### Docker Development
```bash
# Local development with hot reload
docker-compose -f docker-compose.dev.yml up -d

# Test environment (different ports to avoid conflicts)
docker-compose up -d  # Uses ports 8002, 5555, 7333, 7379

# Production deployment
docker-compose -f guka-ai-agent/docker-compose.production.yml up -d
```

### Environment Configuration
- `.env` file required with `CEREBRAS_API_KEY` and `DJANGO_BASE_URL`
- Environment variables are **case-sensitive** (e.g., `CEREBRAS_API_KEY` not `cerebras_api_key`)
- Cache directories must be writable: `TRANSFORMERS_CACHE=/tmp/transformers_cache`

### Testing & Debugging
```bash
# Run health checks
curl http://localhost:8002/health

# Test chat endpoint
curl -X POST http://localhost:8002/chat -H "Content-Type: application/json" \
  -d '{"message": "Hello farmer", "user_id": "test", "session_id": "session"}'

# Check logs
docker-compose logs --tail=50 gukas-agent
```

## Common Issues & Solutions

### Permission Errors
AI model downloads need writable cache directories. Always include:
```yaml
environment:
  - TRANSFORMERS_CACHE=/tmp/transformers_cache
  - HF_HOME=/tmp/huggingface_cache
  - SENTENCE_TRANSFORMERS_HOME=/tmp/sentence_transformers_cache
```

### Missing Dependencies
Ensure `aiofiles==23.2.0` is in `requirements.txt` for document processing.

### Qdrant Health Checks
Qdrant containers often show "unhealthy" due to missing `wget`/`curl`. Use `--no-deps` flag:
```bash
docker-compose up -d --no-deps gukas-agent
```

### Django Integration
- JWT tokens from Django backend for user authentication
- Auto-sync farmer context via `DJANGO_API_TOKEN`
- Health endpoint checks all service dependencies

## File Organization Conventions

- **Models**: `app/models/api_models.py` (Pydantic), `app/models/memory.py` (SQLAlchemy)
- **Services**: One service per file in `app/services/`
- **Database**: Connection management in `app/database.py`
- **Config**: Environment handling in `app/config.py` using pydantic-settings
- **Tests**: `tests/` directory with pytest-asyncio for async testing

When modifying the system, always consider the startup sequence: database connections → vector services → document services → health checks.
