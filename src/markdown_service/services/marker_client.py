"""
Marker API client for document to markdown conversion.
"""
import os
import mimetypes
import asyncio
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

import httpx
import aiofiles
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from ..core.config import get_settings
from ..core.security import SecurityManager

logger = structlog.get_logger(__name__)
settings = get_settings()


class MarkerAPIClient:
    """Client for interacting with the Marker API."""
    
    def __init__(self):
        """Initialize the client."""
        self.security_manager = SecurityManager()
        self.base_url = settings.marker_api_url.rstrip('/')  # Remove trailing slash
        self.timeout = httpx.Timeout(settings.request_timeout)
        self.headers = self.security_manager.get_marker_headers()
    
    def _detect_mime_type(self, filepath: Path) -> str:
        """Detect MIME type of file."""
        mime_type, _ = mimetypes.guess_type(str(filepath))
        if mime_type is None:
            # Default to application/octet-stream if can't detect
            return 'application/octet-stream'
        return mime_type
    
    @retry(
        stop=stop_after_attempt(settings.retry_attempts),
        wait=wait_exponential(multiplier=settings.retry_delay),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException))
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make an HTTP request to the Marker API with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments for the request
            
        Returns:
            httpx.Response
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method,
                    url,
                    headers=self.headers,
                    **kwargs
                )
                response.raise_for_status()
                return response
            except httpx.HTTPError as e:
                logger.error(
                    "Marker API request failed",
                    error=str(e),
                    status_code=getattr(e.response, 'status_code', None),
                    url=url,
                    method=method
                )
                raise
    
    async def convert_to_markdown(
        self,
        file_path: Path
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Convert a document to markdown using the Marker API.
        
        Args:
            file_path: Path to the file to convert
            
        Returns:
            Tuple of (success, markdown_content, error_message)
        """
        try:
            # Detect MIME type
            mime_type = self._detect_mime_type(file_path)
            
            # Read file content
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            
            # Prepare multipart form data
            files = {
                'file': (file_path.name, content, mime_type),  # Include MIME type
                'output_format': (None, 'markdown')
            }
            
            # Make direct request to marker API without endpoint
            url = self.base_url.rstrip('/')  # Ensure no trailing slash
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    files=files,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()
            
            # If conversion is immediate, return result
            if result.get("markdown"):
                return True, result["markdown"], None
            
            # If async conversion, poll for result
            if result.get("request_check_url"):
                poll_result = await self._poll_result(result["request_check_url"])
                if poll_result.get("markdown"):
                    return True, poll_result["markdown"], None
            
            return False, None, "Invalid response from Marker API"
            
        except Exception as e:
            logger.error(
                "Document conversion failed",
                error=str(e),
                file=str(file_path)
            )
            return False, None, str(e)
    
    async def _poll_result(
        self,
        check_url: str,
        max_attempts: int = settings.max_polls,
        interval: int = settings.poll_interval
    ) -> Dict[str, Any]:
        """
        Poll for conversion result.
        
        Args:
            check_url: URL to check status (complete URL, not endpoint)
            max_attempts: Maximum number of polling attempts
            interval: Seconds between polling attempts
            
        Returns:
            Dict with conversion result
            
        Raises:
            TimeoutError: If polling exceeds max attempts
            ValueError: If conversion fails
        """
        for attempt in range(max_attempts):
            try:
                await asyncio.sleep(interval)
                
                # Direct GET request to the check_url (which is a complete URL)
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        check_url,
                        headers=self.headers
                    )
                    response.raise_for_status()
                    result = response.json()
                
                if result.get("status") == "complete":
                    return result
                elif result.get("status") == "error":
                    raise ValueError(f"Conversion failed: {result.get('error')}")
                    
            except Exception as e:
                logger.error(
                    "Status check failed",
                    error=str(e),
                    attempt=attempt,
                    check_url=check_url
                )
                raise
        
        raise TimeoutError(
            f"Polling timed out after {max_attempts * interval} seconds"
        )
    
