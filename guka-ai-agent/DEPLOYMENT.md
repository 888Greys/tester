# 🚀 Guka AI Agent - Server Deployment Guide

## 📋 **Prerequisites**

Your server should have:
- **Docker** and **Docker Compose** installed
- **Git** installed
- At least **4GB RAM** and **20GB disk space**
- **Port 8001** available for the API

## 📥 **Step 1: Clone the Repository**

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/guka-ai-agent.git
cd guka-ai-agent

# Or if you already have it, pull latest changes
git pull origin main
```

## ⚙️ **Step 2: Environment Configuration**

```bash
# Copy environment template
cp .env.example .env

# Edit the environment file
nano .env  # or use vim/vi
```

**Required configuration in `.env`:**

```env
# Cerebras API Configuration (REQUIRED)
CEREBRAS_API_KEY=your_cerebras_api_key_here
CEREBRAS_BASE_URL=https://api.cerebras.ai/v1
CEREBRAS_MODEL=gpt-oss-120b

# Django Backend Integration
DJANGO_BASE_URL=https://gukasbackend.brand2d.tech
DJANGO_API_TOKEN=your_django_jwt_token_here

# Application Configuration
APP_NAME=Gukas AI Agent
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=8001

# Database Configuration (Docker containers)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=gukas_memory
POSTGRES_USER=gukas_user
POSTGRES_PASSWORD=gukas_secure_password_2024

# Qdrant Vector Database
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

## 🏗️ **Step 3: Deploy with Docker**

```bash
# Enable BuildKit for faster builds (optional)
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Start all services
docker-compose up --build -d

# This will start:
# - PostgreSQL database (port 5432)
# - Qdrant vector database (ports 6333, 6334)
# - Redis cache (port 6379)
# - Gukas AI Agent (port 8001)
```

## 🔍 **Step 4: Verify Deployment**

```bash
# Check all containers are running
docker-compose ps

# Check logs
docker-compose logs -f gukas-agent

# Test health endpoint
curl http://localhost:8001/health

# Test service info
curl http://localhost:8001/info
```

Expected response from `/health`:
```json
{
  "status": "healthy",
  "app_name": "Gukas AI Agent",
  "version": "1.0.0",
  "dependencies": {
    "cerebras_api": "connected",
    "postgres": "connected",
    "qdrant": "connected",
    "redis": "connected"
  }
}
```

## 📄 **Step 5: Test Document Upload**

```bash
# Upload a test document
curl -X POST http://localhost:8001/documents/upload \
  -F "file=@test_coffee_document.txt" \
  -F "user_id=admin" \
  -F "description=Coffee farming guide" \
  -F "tags=coffee,farming,guide"

# Test document search
curl -X POST http://localhost:8001/documents/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "coffee leaf rust treatment",
    "limit": 3
  }'

# Test RAG-enhanced chat
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I treat coffee diseases?",
    "user_id": "farmer_123",
    "session_id": "test_session"
  }'
```

## 🛠️ **Management Commands**

```bash
# View logs
docker-compose logs -f
docker-compose logs -f gukas-agent    # Just the main app
docker-compose logs -f postgres       # Database logs

# Restart services
docker-compose restart gukas-agent

# Stop all services
docker-compose down

# Stop and remove all data (DESTRUCTIVE)
docker-compose down -v

# Update from GitHub
git pull origin main
docker-compose up --build -d
```

## 📊 **Monitoring**

### Container Health
```bash
# Check container status
docker-compose ps

# Check resource usage
docker stats

# Check disk usage
docker system df
```

### Application Health
```bash
# Health check
curl http://localhost:8001/health

# Service info
curl http://localhost:8001/info

# List documents
curl http://localhost:8001/documents
```

## 🔒 **Security Notes**

1. **Firewall**: Only expose port 8001 externally
2. **Environment**: Set `DEBUG=false` in production
3. **API Keys**: Keep your Cerebras API key secure
4. **Database**: Change default passwords in `.env`
5. **Updates**: Regularly update with `git pull && docker-compose up --build -d`

## 🐛 **Troubleshooting**

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using the port
   sudo netstat -tulnp | grep 8001
   sudo lsof -i :8001
   ```

2. **Database connection errors**
   ```bash
   # Check database container
   docker-compose logs postgres
   
   # Verify database is healthy
   docker-compose ps
   ```

3. **Memory issues**
   ```bash
   # Check available memory
   free -h
   
   # Check Docker memory usage
   docker stats
   ```

4. **Build failures**
   ```bash
   # Clean Docker cache
   docker system prune -a
   
   # Rebuild from scratch
   docker-compose down -v
   docker-compose up --build -d
   ```

### Debug Mode
Enable debug logging:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

Then restart:
```bash
docker-compose restart gukas-agent
docker-compose logs -f gukas-agent
```

## 📱 **API Endpoints**

Once deployed, your API will be available at:

- **Health**: `http://your-server:8001/health`
- **Chat**: `http://your-server:8001/chat`
- **Document Upload**: `http://your-server:8001/documents/upload`
- **Document Search**: `http://your-server:8001/documents/search`
- **API Docs**: `http://your-server:8001/docs` (if DEBUG=true)

## 🔄 **Updates**

To update the system:
```bash
cd guka-ai-agent
git pull origin main
docker-compose up --build -d
```

---

🌱 **Your Guka AI Agent with Document Intelligence is now ready to help farmers!**
