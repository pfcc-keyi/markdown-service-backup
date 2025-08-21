"""
File management service for temporary file handling and orchestrator integration.
"""
import os
import uuid
import asyncio
import base64
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse

import aiofiles
import structlog
import httpx

from ..core.config import get_settings
from ..models.api import OutputMethod

logger = structlog.get_logger(__name__)
settings = get_settings()


class FileManager:
    """Secure file management with orchestrator integration."""
    
    def __init__(self):
        """Initialize file manager."""
        self.temp_dir = Path(settings.temp_dir)
        self.max_file_size = settings.max_file_size
        self.output_dir = self.temp_dir / "outputs"
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure temporary and output directories exist."""
        try:
            # Create temp directory
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Create output directory for storing results
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = self.temp_dir / f"test_{uuid.uuid4().hex[:8]}.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            logger.info(f"Directories initialized - temp: {self.temp_dir}, output: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Failed to initialize directories: {e}")
            raise RuntimeError(f"Cannot create or write to directories: {e}")
    
    async def process_input(self, file_content: Optional[str] = None, 
                          file_url: Optional[str] = None, 
                          filename: str = "") -> Tuple[Path, Dict[str, Any]]:
        """
        Process file input from various sources.
        
        Args:
            file_content: Base64 encoded file content
            file_url: URL to download file from
            filename: Original filename
            
        Returns:
            Tuple of (temp_file_path, file_metadata)
        """
        if file_content:
            return await self._process_base64_input(file_content, filename)
        elif file_url:
            return await self._process_url_input(file_url, filename)
        else:
            raise ValueError("Either file_content or file_url must be provided")
    
    async def _process_base64_input(self, file_content: str, filename: str) -> Tuple[Path, Dict[str, Any]]:
        """Process base64 encoded file content."""
        try:
            # Decode base64 content
            file_bytes = base64.b64decode(file_content)
            
            # Validate file size
            if len(file_bytes) > self.max_file_size:
                raise ValueError(f"File too large: {len(file_bytes)} bytes")
            
            # Store file
            temp_path = await self.store_upload(file_bytes, filename)
            
            # Generate metadata
            metadata = {
                "source": "base64",
                "size": len(file_bytes),
                "checksum": hashlib.md5(file_bytes).hexdigest()
            }
            
            return temp_path, metadata
            
        except Exception as e:
            logger.error(f"Failed to process base64 input: {e}")
            raise
    
    async def _process_url_input(self, file_url: str, filename: str) -> Tuple[Path, Dict[str, Any]]:
        """Download and process file from URL."""
        try:
            # Validate URL
            parsed = urlparse(file_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid file URL")
            
            # Download file
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(file_url)
                response.raise_for_status()
                
                file_bytes = response.content
                
                # Validate file size
                if len(file_bytes) > self.max_file_size:
                    raise ValueError(f"File too large: {len(file_bytes)} bytes")
                
                # Store file
                temp_path = await self.store_upload(file_bytes, filename)
                
                # Generate metadata
                metadata = {
                    "source": "url",
                    "source_url": file_url,
                    "size": len(file_bytes),
                    "checksum": hashlib.md5(file_bytes).hexdigest(),
                    "content_type": response.headers.get("content-type")
                }
                
                return temp_path, metadata
                
        except Exception as e:
            logger.error(f"Failed to process URL input {file_url}: {e}")
            raise
    
    async def store_upload(self, file_content: bytes, filename: str) -> Path:
        """
        Store uploaded file content to temporary location.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename (for extension)
            
        Returns:
            Path to temporary file
        """
        try:
            # Validate file size
            if len(file_content) > self.max_file_size:
                raise ValueError(f"File too large: {len(file_content)} bytes")
            
            # Generate unique temporary filename
            file_extension = Path(filename).suffix
            temp_filename = f"{uuid.uuid4()}_{filename}"
            temp_path = self.temp_dir / temp_filename
            
            # Write file asynchronously
            async with aiofiles.open(temp_path, 'wb') as f:
                await f.write(file_content)
            
            # Verify file was written correctly
            if not temp_path.exists():
                raise RuntimeError("Failed to write temporary file")
            
            actual_size = temp_path.stat().st_size
            if actual_size != len(file_content):
                raise RuntimeError(f"File size mismatch: expected {len(file_content)}, got {actual_size}")
            
            logger.info(
                "File stored successfully",
                temp_path=str(temp_path),
                size=actual_size,
                original_filename=filename
            )
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to store file: {e}")
            raise
    
    async def store_output(self, content: str, filename: str, 
                          output_method: OutputMethod, max_inline_size: int) -> Tuple[OutputMethod, Optional[str], Optional[str]]:
        """
        Store output content based on the specified method.
        
        Args:
            content: Content to store
            filename: Base filename
            output_method: How to handle output
            max_inline_size: Maximum size for inline content
            
        Returns:
            Tuple of (actual_method, inline_content, reference_url)
        """
        content_size = len(content.encode('utf-8'))
        
        # Decide output method
        if output_method == OutputMethod.AUTO:
            actual_method = OutputMethod.INLINE if content_size <= max_inline_size else OutputMethod.REFERENCE
        else:
            actual_method = output_method
        
        if actual_method == OutputMethod.INLINE:
            # Return content directly
            return actual_method, content, None
        else:
            # Store content and return reference
            output_filename = f"{Path(filename).stem}_{uuid.uuid4().hex[:8]}.md"
            output_path = self.output_dir / output_filename
            
            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            # Generate URL/reference (this would be service-specific)
            reference_url = f"/outputs/{output_filename}"
            
            logger.info(f"Output stored to {output_path}, size: {content_size} bytes")
            
            return actual_method, None, reference_url
    
    def cleanup_file(self, file_path: Path) -> bool:
        """
        Safely delete temporary file.
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if successfully deleted, False otherwise
        """
        try:
            if file_path and file_path.exists():
                # Ensure file is in our temp directory (security check)
                if not str(file_path).startswith(str(self.temp_dir)):
                    logger.warning(f"Attempted to delete file outside temp directory: {file_path}")
                    return False
                
                file_path.unlink()
                logger.debug(f"Temporary file deleted: {file_path}")
                return True
            else:
                logger.debug(f"File does not exist, nothing to cleanup: {file_path}")
                return True
                
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {e}")
            return False
    
    async def cleanup_file_async(self, file_path: Path) -> bool:
        """Async version of cleanup_file."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.cleanup_file, file_path)
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age in hours before deletion
            
        Returns:
            Number of files deleted
        """
        try:
            import time
            
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            deleted_count = 0
            
            # Clean both temp and output directories
            for directory in [self.temp_dir, self.output_dir]:
                for file_path in directory.iterdir():
                    if file_path.is_file():
                        try:
                            file_age = current_time - file_path.stat().st_mtime
                            if file_age > max_age_seconds:
                                file_path.unlink()
                                deleted_count += 1
                                logger.debug(f"Deleted old file: {file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to delete old file {file_path}: {e}")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old files")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            return 0
    
    def get_temp_dir_info(self) -> dict:
        """Get information about temporary directory usage."""
        try:
            temp_file_count = len(list(self.temp_dir.glob('*')))
            output_file_count = len(list(self.output_dir.glob('*')))
            
            # Calculate total size
            total_size = 0
            for directory in [self.temp_dir, self.output_dir]:
                for file_path in directory.iterdir():
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            
            # Get disk usage
            stat = os.statvfs(self.temp_dir)
            free_space = stat.f_bavail * stat.f_frsize
            total_space = stat.f_blocks * stat.f_frsize
            
            return {
                "temp_dir": str(self.temp_dir),
                "output_dir": str(self.output_dir),
                "temp_file_count": temp_file_count,
                "output_file_count": output_file_count,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "free_space_mb": round(free_space / (1024 * 1024), 2),
                "total_space_mb": round(total_space / (1024 * 1024), 2),
                "usage_percent": round((total_space - free_space) / total_space * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get temp dir info: {e}")
            return {"error": str(e)} 