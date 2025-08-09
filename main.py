"""
Main entry point for the Gukas AI Agent.
Starts the FastAPI server with proper configuration.
"""

import uvicorn
from app.config import settings
from app.api import app

if __name__ == "__main__":
    print(f"🌱 Starting {settings.app_name} v{settings.app_version}")
    print(f"🔧 Debug mode: {settings.debug}")
    print(f"🧠 Cerebras model: {settings.cerebras_model}")
    print(f"🌐 Server: http://{settings.host}:{settings.port}")
    print(f"📚 Docs: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run(
        "app.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )