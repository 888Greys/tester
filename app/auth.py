"""
Service-to-service authentication for AI Agent.
Provides JWT-based authentication for secure communication between Django and AI Agent.
"""

import jwt
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

logger = logging.getLogger(__name__)

# Security scheme for FastAPI
security = HTTPBearer()

class ServiceAuth:
    """Service authentication handler."""
    
    @staticmethod
    def generate_service_token(service_name: str, expires_hours: int = 24) -> str:
        """Generate a JWT token for service-to-service communication."""
        payload = {
            "service": service_name,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=expires_hours),
            "type": "service_token"
        }
        
        token = jwt.encode(
            payload, 
            settings.service_secret_key, 
            algorithm="HS256"
        )
        
        logger.info(f"Generated service token for {service_name}")
        return token
    
    @staticmethod
    def verify_service_token(token: str) -> Dict[str, Any]:
        """Verify and decode a service JWT token."""
        try:
            payload = jwt.decode(
                token, 
                settings.service_secret_key, 
                algorithms=["HS256"]
            )
            
            # Check token type
            if payload.get("type") != "service_token":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            logger.debug(f"Verified service token for {payload.get('service')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Service token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid service token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    @staticmethod
    def verify_django_service(token: str) -> Dict[str, Any]:
        """Verify token is from Django backend service."""
        payload = ServiceAuth.verify_service_token(token)
        
        if payload.get("service") != "django_backend":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized service"
            )
        
        return payload


# FastAPI dependency for service authentication
async def authenticate_service(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """FastAPI dependency to authenticate service requests."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    return ServiceAuth.verify_django_service(credentials.credentials)


# Optional authentication (for endpoints that can work with or without auth)
async def optional_service_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[Dict[str, Any]]:
    """Optional service authentication for endpoints that can work without auth."""
    if not credentials:
        return None
    
    try:
        return ServiceAuth.verify_django_service(credentials.credentials)
    except HTTPException:
        # Log the failed auth but don't raise exception
        logger.warning("Optional service authentication failed")
        return None


# Utility functions
def generate_django_token() -> str:
    """Generate a token for Django backend service."""
    return ServiceAuth.generate_service_token("django_backend", expires_hours=24)


def is_authenticated_request(auth_data: Optional[Dict[str, Any]]) -> bool:
    """Check if request is authenticated."""
    return auth_data is not None and auth_data.get("service") == "django_backend"