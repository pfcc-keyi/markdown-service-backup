"""
Security management for the Markdown Service.
"""
import os
from pathlib import Path
from typing import Dict, Optional

import structlog
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

from .config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Define security scheme for service token
service_token_header = APIKeyHeader(name="X-Service-Token", auto_error=False)


class SecurityManager:
    """Manages security aspects of the service."""
    
    def __init__(self):
        """Initialize security manager."""
        self._marker_api_key = self._load_marker_api_key()
        self._service_token = self._load_service_token()
    
    def _load_marker_api_key(self) -> str:
        """
        Load Marker API key with the following priority:
        1. Kubernetes secret
        2. Environment variable
        3. Configuration file
        """
        # Try Kubernetes secret first
        secret_path = Path("/var/secrets/marker/api-key")
        if secret_path.exists():
            try:
                return secret_path.read_text().strip()
            except Exception as e:
                logger.error("Failed to read Marker API key from secret", error=str(e))
        
        # Try environment variable
        if api_key := os.getenv("MARKER_API_KEY"):
            return api_key
        
        # Use configuration
        if settings.dev_mode:
            return "dev-key"
        
        raise ValueError("Marker API key not found")
    
    def _load_service_token(self) -> str:
        """
        Load service token with the following priority:
        1. Kubernetes secret
        2. Environment variable
        3. Configuration file
        """
        # Try Kubernetes secret first
        secret_path = Path("/var/secrets/service/token")
        if secret_path.exists():
            try:
                return secret_path.read_text().strip()
            except Exception as e:
                logger.error("Failed to read service token from secret", error=str(e))
        
        # Try environment variable
        if token := os.getenv("SERVICE_TOKEN"):
            return token
        
        # Use configuration
        if settings.dev_mode:
            return "dev-token"
        
        # Fallback: return empty string (will cause 401 on auth but won't crash startup)
        logger.warning("Service token not found, using empty string")
        return ""
    
    def get_marker_headers(self) -> Dict[str, str]:
        """Get headers for Marker API requests."""
        return {
            "X-Api-Key": self._marker_api_key,
            "User-Agent": f"{settings.service_name}/{settings.service_version}"
        }
    
    async def validate_service_token(
        self,
        token: Optional[str] = Security(service_token_header)
    ) -> bool:
        """
        Validate service token from request header.
        
        Args:
            token: Service token from request header
            
        Returns:
            bool: True if token is valid
            
        Raises:
            HTTPException: If token is invalid
        """
        # Skip validation in dev mode
        if settings.dev_mode:
            return True
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Service token required"
            )
        
        if token != self._service_token:
            raise HTTPException(
                status_code=401,
                detail="Invalid service token"
            )
        
        return True
    
    def get_masked_marker_key(self) -> str:
        """Get masked version of Marker API key for logging."""
        if not self._marker_api_key:
            return "not-set"
        if len(self._marker_api_key) <= 8:
            return "*" * len(self._marker_api_key)
        return f"{self._marker_api_key[:4]}...{self._marker_api_key[-4:]}"
