"""
Configuration management for the markdown service.
"""
import os
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service configuration
    service_name: str = "markdown-service"
    service_version: str = "1.0.0"
    port: int = Field(default=8002, env="PORT")
    host: str = Field(default="0.0.0.0", env="HOST")
    
    # Marker API configuration
    marker_api_key: str = Field(..., env="MARKER_API_KEY")
    marker_api_url: str = Field(
        default="https://www.datalab.to/api/v1/marker",
        env="MARKER_API_URL"
    )
    
    # File processing configuration
    temp_dir: str = Field(default="/tmp/markdown-service", env="TEMP_DIR")
    max_file_size: int = Field(default=52428800, env="MAX_FILE_SIZE")  # 50MB
    
    # API configuration
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")  # 5 minutes
    poll_interval: int = Field(default=2, env="POLL_INTERVAL")  # 2 seconds
    max_polls: int = Field(default=300, env="MAX_POLLS")  # 10 minutes total
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Health check
    health_check_timeout: int = Field(default=10, env="HEALTH_CHECK_TIMEOUT")
    
    # Security and authentication
    service_token: str = Field(default="", env="SERVICE_TOKEN")
    
    # Development mode settings
    dev_mode: bool = Field(default=False, env="DEV_MODE")
    
    # Rate limiting and retry
    retry_attempts: int = Field(default=3, env="RETRY_ATTEMPTS")
    retry_delay: float = Field(default=1.0, env="RETRY_DELAY")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings 