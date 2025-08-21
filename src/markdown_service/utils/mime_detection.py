"""
MIME type detection utilities.
"""
import mimetypes
from pathlib import Path
from typing import Optional

import filetype
import structlog

logger = structlog.get_logger(__name__)


class MimeTypeDetector:
    """MIME type detection with multiple fallback methods."""
    
    # Supported MIME types mapping
    SUPPORTED_TYPES = {
        'application/pdf': 'pdf',
        'application/msword': 'doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'text/plain': 'txt',
    }
    
    def __init__(self):
        """Initialize MIME type detector."""
        # Initialize mimetypes database
        mimetypes.init()
    
    def detect_from_filename(self, filename: str) -> Optional[str]:
        """Detect MIME type from filename extension."""
        try:
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type in self.SUPPORTED_TYPES:
                logger.debug(f"MIME type detected from filename: {mime_type}")
                return mime_type
        except Exception as e:
            logger.warning(f"Failed to detect MIME type from filename: {e}")
        
        return None
    
    def detect_from_content(self, file_content: bytes) -> Optional[str]:
        """Detect MIME type from file content using filetype library."""
        try:
            kind = filetype.guess(file_content)
            if kind is not None:
                mime_type = kind.mime
                if mime_type in self.SUPPORTED_TYPES:
                    logger.debug(f"MIME type detected from content: {mime_type}")
                    return mime_type
        except Exception as e:
            logger.warning(f"Failed to detect MIME type from content: {e}")
        
        return None
    
    def detect_from_extension(self, filename: str) -> Optional[str]:
        """Fallback: detect MIME type from file extension manually."""
        try:
            extension = Path(filename).suffix.lower()
            extension_map = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.txt': 'text/plain',
            }
            
            mime_type = extension_map.get(extension)
            if mime_type:
                logger.debug(f"MIME type detected from extension: {mime_type}")
                return mime_type
        except Exception as e:
            logger.warning(f"Failed to detect MIME type from extension: {e}")
        
        return None
    
    def detect(self, filename: str, file_content: Optional[bytes] = None) -> str:
        """
        Comprehensive MIME type detection with multiple methods.
        
        Priority order:
        1. Content-based detection (if file_content provided)
        2. Filename-based detection
        3. Extension-based fallback
        """
        # Method 1: Content-based detection
        if file_content:
            mime_type = self.detect_from_content(file_content)
            if mime_type:
                return mime_type
        
        # Method 2: Filename-based detection
        mime_type = self.detect_from_filename(filename)
        if mime_type:
            return mime_type
        
        # Method 3: Extension-based fallback
        mime_type = self.detect_from_extension(filename)
        if mime_type:
            return mime_type
        
        # If all methods fail, raise an error
        raise ValueError(f"Unsupported file type for: {filename}")
    
    def is_supported(self, mime_type: str) -> bool:
        """Check if MIME type is supported."""
        return mime_type in self.SUPPORTED_TYPES
    
    def get_file_format(self, mime_type: str) -> str:
        """Get file format string from MIME type."""
        return self.SUPPORTED_TYPES.get(mime_type, "unknown") 