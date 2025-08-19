# 🧪 Test Deployment Guide

This setup allows you to test the new Document Intelligence features alongside your existing production containers without conflicts.

## 📋 **Test Configuration**

The test environment uses different:
- **Container names**: All containers have `-test` suffix
- **Ports**: Different ports to avoid conflicts with production
- **Volumes**: Separate data volumes for isolation
- **Network**: Separate Docker network (`gukas-test-network`)

### Port Mapping:
| Service | Production Port | Test Port |
|---------|----------------|-----------|
| Gukas AI Agent | 8001 | **8002** |
| PostgreSQL | 5432 | **5555** |
| Qdrant | 6333/6334 | **7333/7334** |
| Redis | 6379 | **7379** |

### Container Names:
- `gukas-ai-agent-test`
- `gukas-postgres-test`
- `gukas-qdrant-test`
- `gukas-redis-test`

## 🚀 **Deploy Test Environment**

### On Your Server:

1. **Clone/Update Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/guka-ai-agent.git
   cd guka-ai-agent
   # OR
   git pull origin main
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Add your Cerebras API key
   ```

3. **Deploy Test Environment**
   ```bash
   # Start test containers (uses docker-compose.yml by default)
   docker-compose up --build -d
   
   # Check all containers are running
   docker-compose ps
   
   # Check logs
   docker-compose logs -f gukas-agent
   ```

4. **Test the API**
   ```bash
   # Health check (note the different port)
   curl http://localhost:8002/health
   
   # Service info
   curl http://localhost:8002/info
   ```

## 📄 **Test Document Upload**

1. **Upload test document**
   ```bash
   curl -X POST http://localhost:8002/documents/upload \
     -F "file=@test_coffee_document.txt" \
     -F "user_id=admin" \
     -F "description=Test coffee farming guide" \
     -F "tags=coffee,farming,test"
   ```

2. **Search documents**
   ```bash
   curl -X POST http://localhost:8002/documents/search \
     -H "Content-Type: application/json" \
     -d '{
       "query": "coffee leaf rust treatment",
       "limit": 3
     }'
   ```

3. **Test RAG-enhanced chat**
   ```bash
   curl -X POST http://localhost:8002/chat \
     -H "Content-Type: application/json" \
     -d '{
       "message": "How do I treat coffee diseases?",
       "user_id": "farmer_123",
       "session_id": "test_session"
     }'
   ```

## 🔄 **Switch to Production**

Once testing is successful, switch to production:

1. **Stop test containers**
   ```bash
   docker-compose down
   ```

2. **Deploy production version**
   ```bash
   # Use production compose file with normal ports/names
   docker-compose -f docker-compose.production.yml up --build -d
   
   # Production will be available on:
   # http://localhost:8001 (normal port)
   ```

3. **Clean up test environment (optional)**
   ```bash
   # Remove test containers and volumes
   docker-compose down -v
   
   # Remove test images
   docker rmi gukas-ai-agent:test
   ```

## 🛠️ **Management Commands**

### Test Environment:
```bash
# View logs
docker-compose logs -f

# Stop test environment
docker-compose down

# Restart specific service
docker-compose restart gukas-agent
```

### Production Environment:
```bash
# View production logs
docker-compose -f docker-compose.production.yml logs -f

# Stop production
docker-compose -f docker-compose.production.yml down

# Update production
git pull origin main
docker-compose -f docker-compose.production.yml up --build -d
```

## 📊 **Verify Both Environments**

You can run both test and production simultaneously:

### Check Test (Port 8002):
```bash
curl http://localhost:8002/health
curl http://localhost:8002/info
```

### Check Production (Port 8001):
```bash
curl http://localhost:8001/health
curl http://localhost:8001/info
```

## 🧹 **Cleanup**

### Remove test environment only:
```bash
docker-compose down -v
docker rmi gukas-ai-agent:test
```

### Remove everything (CAREFUL!):
```bash
# Stop all
docker-compose down -v
docker-compose -f docker-compose.production.yml down -v

# Remove images
docker rmi gukas-ai-agent:test gukas-ai-agent:latest
```

---

This setup allows you to safely test the new Document Intelligence features without affecting your production environment!
