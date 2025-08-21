"""
Input validation utilities.
"""
import base64
import hashlib
from pathlib import Path
from typing import Tuple

import structlog

from ..core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class FileValidator:
    """File validation utilities."""
    
    def __init__(self):
        """Initialize file validator."""
        self.max_file_size = settings.max_file_size
        self.supported_extensions = ['.pdf', '.docx', '.doc', '.txt']
    
    def validate_file_size(self, file_content: bytes) -> bool:
        """Validate file size is within limits."""
        file_size = len(file_content)
        
        if file_size == 0:
            raise ValueError("File is empty")
        
        if file_size > self.max_file_size:
            max_mb = self.max_file_size / (1024 * 1024)
            current_mb = file_size / (1024 * 1024)
            raise ValueError(
                f"File too large: {current_mb:.1f}MB (max: {max_mb:.1f}MB)"
            )
        
        logger.debug(f"File size validation passed: {file_size} bytes")
        return True
    
    def validate_filename(self, filename: str) -> bool:
        """Validate filename format and extension."""
        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")
        
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                raise ValueError(f"Filename contains invalid character: {char}")
        
        # Check extension
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        if extension not in self.supported_extensions:
            raise ValueError(
                f"Unsupported file extension: {extension}. "
                f"Supported: {self.supported_extensions}"
            )
        
        logger.debug(f"Filename validation passed: {filename}")
        return True
    
    def validate_base64_content(self, content: str) -> bytes:
        """Validate and decode base64 content."""
        try:
            # Remove any whitespace/newlines
            content = content.strip().replace('\n', '').replace('\r', '')
            
            # Decode base64
            file_content = base64.b64decode(content)
            
            # Validate decoded content
            if len(file_content) == 0:
                raise ValueError("Decoded file content is empty")
            
            logger.debug(f"Base64 validation passed: {len(file_content)} bytes")
            return file_content
            
        except Exception as e:
            raise ValueError(f"Invalid base64 content: {e}")
    
    def calculate_checksum(self, file_content: bytes) -> str:
        """Calculate MD5 checksum for file integrity."""
        try:
            md5_hash = hashlib.md5()
            md5_hash.update(file_content)
            checksum = md5_hash.hexdigest()
            logger.debug(f"File checksum calculated: {checksum}")
            return checksum
        except Exception as e:
            logger.warning(f"Failed to calculate checksum: {e}")
            return ""
    
    def validate_file(self, filename: str, base64_content: str) -> Tuple[bytes, str]:
        """
        Comprehensive file validation.
        
        Returns:
            Tuple of (decoded_content, checksum)
        """
        # Validate filename
        self.validate_filename(filename)
        
        # Validate and decode content
        file_content = self.validate_base64_content(base64_content)
        
        # Validate file size
        self.validate_file_size(file_content)
        
        # Calculate checksum
        checksum = self.calculate_checksum(file_content)
        
        logger.info(
            "File validation completed",
            filename=filename,
            size=len(file_content),
            checksum=checksum[:8]  # First 8 chars for logging
        )
        
        return file_content, checksum


class RequestValidator:
    """Request validation utilities."""
    
    @staticmethod
    def validate_request_id(request_id: str) -> bool:
        """Validate request ID format."""
        if not request_id:
            return True  # Optional field
        
        # Basic format validation
        if len(request_id) < 8 or len(request_id) > 128:
            raise ValueError("Request ID must be between 8 and 128 characters")
        
        # Allow alphanumeric, hyphens, and underscores
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
        if not all(c in allowed_chars for c in request_id):
            raise ValueError("Request ID contains invalid characters")
        
        return True 