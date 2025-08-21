"""
API data models for request and response validation.
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
import base64


class FileFormat(str, Enum):
    """Supported file formats for conversion."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"


class InputMethod(str, Enum):
    """Input method for file processing."""
    UPLOAD = "upload"  # Direct file upload
    BASE64 = "base64"  # Base64 encoded content
    URL = "url"       # File URL reference


class OutputMethod(str, Enum):
    """Output method for results."""
    INLINE = "inline"    # Return content directly
    REFERENCE = "reference"  # Return URL/path reference
    AUTO = "auto"        # Decide based on content size


class ConvertRequest(BaseModel):
    """Request model for document conversion."""
    # Input options
    file_content: Optional[str] = Field(None, description="Base64 encoded file content")
    file_url: Optional[str] = Field(None, description="URL to file for processing")
    filename: str = Field(..., description="Original filename with extension")
    content_type: Optional[str] = Field(None, description="MIME type (auto-detected if not provided)")
    
    # Processing options
    request_id: Optional[str] = Field(None, description="Orchestrator request ID for tracking")
    output_method: OutputMethod = Field(OutputMethod.AUTO, description="How to return results")
    max_inline_size: int = Field(1024*1024, description="Max size for inline content (bytes)")
    
    # Orchestrator integration
    callback_url: Optional[str] = Field(None, description="Callback URL for async processing")
    priority: int = Field(5, description="Processing priority (1=highest, 10=lowest)")
    
    @validator("file_content")
    def validate_base64_content(cls, v: Optional[str]) -> Optional[str]:
        """Validate that file_content is valid base64."""
        if v is None:
            return v
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("file_content must be valid base64 encoded data")
    
    @validator("filename")
    def validate_filename(cls, v: str) -> str:
        """Validate filename format and extension."""
        if not v or len(v.strip()) == 0:
            raise ValueError("filename cannot be empty")
        
        # Check for supported extensions
        supported_extensions = ['.pdf', '.docx', '.doc', '.txt']
        if not any(v.lower().endswith(ext) for ext in supported_extensions):
            raise ValueError(f"Unsupported file format. Supported: {supported_extensions}")
        
        return v.strip()
    
    @validator("priority")
    def validate_priority(cls, v: int) -> int:
        """Validate priority range."""
        if not 1 <= v <= 10:
            raise ValueError("Priority must be between 1 (highest) and 10 (lowest)")
        return v


class ConvertResponse(BaseModel):
    """Response model for document conversion."""
    success: bool = Field(..., description="Whether the conversion was successful")
    
    # Content options
    markdown_content: Optional[str] = Field(None, description="Converted markdown content (if inline)")
    markdown_url: Optional[str] = Field(None, description="URL to markdown file (if reference)")
    content_size: Optional[int] = Field(None, description="Size of converted content in bytes")
    
    # Metadata
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    processing_time: float = Field(..., description="Processing time in seconds")
    file_info: Dict[str, Any] = Field(default_factory=dict, description="File metadata")
    
    # Error handling
    error: Optional[str] = Field(None, description="Error message if conversion failed")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    # Orchestrator integration
    output_method: OutputMethod = Field(..., description="How results were returned")


class ConversionStatus(str, Enum):
    """Conversion status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StatusResponse(BaseModel):
    """Response model for conversion status check."""
    task_id: str = Field(..., description="Task identifier")
    status: ConversionStatus = Field(..., description="Current conversion status")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    result: Optional[ConvertResponse] = Field(None, description="Result if completed")
    created_at: str = Field(..., description="Task creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheck(BaseModel):
    """Health check response model."""
    status: HealthStatus = Field(..., description="Overall health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Health check timestamp")
    checks: Dict[str, Any] = Field(..., description="Individual health checks")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request identifier")
    timestamp: str = Field(..., description="Error timestamp")


class FileMetadata(BaseModel):
    """File metadata information."""
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    format: FileFormat = Field(..., description="File format")
    checksum: Optional[str] = Field(None, description="File checksum for integrity")


class MarkerAPIResponse(BaseModel):
    """Internal model for Marker API response."""
    success: bool
    request_check_url: Optional[str] = None
    error: Optional[str] = None
    markdown: Optional[str] = None
    status: Optional[str] = None


# Orchestrator integration models
class TaskSubmission(BaseModel):
    """Model for task submission to orchestrator."""
    service: str = Field(..., description="Target service name")
    operation: str = Field(..., description="Operation to perform")
    payload: Dict[str, Any] = Field(..., description="Request payload")
    priority: int = Field(5, description="Task priority")
    callback_url: Optional[str] = Field(None, description="Completion callback")
    timeout: int = Field(300, description="Task timeout in seconds")


class TaskResult(BaseModel):
    """Model for task completion result."""
    task_id: str = Field(..., description="Task identifier")
    service: str = Field(..., description="Service that processed the task")
    status: ConversionStatus = Field(..., description="Final status")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time: float = Field(..., description="Total processing time")
    created_at: str = Field(..., description="Task creation time")
    completed_at: str = Field(..., description="Task completion time") 