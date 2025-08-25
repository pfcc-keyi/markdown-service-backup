"""
Markdown Service main application.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import time

import structlog
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .core.config import get_settings
from .core.security import SecurityManager
from .services.marker_client import MarkerAPIClient
from .services.file_manager import FileManager
from .models.api import (
    ConvertRequest,
    ConvertResponse,
    HealthCheck,
    HealthStatus,
    ErrorResponse,
    OutputMethod
)

# Initialize settings and logger
settings = get_settings()
logger = structlog.get_logger(__name__)

# Initialize security
security_manager = SecurityManager()

# Initialize services
marker_client = MarkerAPIClient()
file_manager = FileManager()

# Create FastAPI app
app = FastAPI(
    title="Markdown Conversion Service",
    description="Convert documents to Markdown format using Marker API",
    version=settings.service_version,
    docs_url="/docs" if settings.dev_mode else None,
    redoc_url="/redoc" if settings.dev_mode else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Add metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """Check service health."""
    try:
        # Check temp directory
        temp_dir = Path(settings.temp_dir)
        temp_dir.mkdir(exist_ok=True)
        temp_dir_writable = os.access(temp_dir, os.W_OK)
        
        # Prepare health check response
        checks = {
            "service_status": True,  # Service is running
            "temp_directory": temp_dir_writable,  # Temp directory is writable
            "marker_api_configured": bool(settings.marker_api_key)  # Check if API key is configured
        }
        
        status = (
            HealthStatus.HEALTHY
            if all(checks.values())
            else HealthStatus.DEGRADED
        )
        
        return HealthCheck(
            status=status,
            service=settings.service_name,
            version=settings.service_version,
            timestamp=datetime.utcnow().isoformat() + "Z",
            checks=checks
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthCheck(
            status=HealthStatus.UNHEALTHY,
            service=settings.service_name,
            version=settings.service_version,
            timestamp=datetime.utcnow().isoformat() + "Z",
            checks={"error": str(e)}
        )


@app.post("/v1/convert", response_model=ConvertResponse)
async def convert_file_upload(
    file: UploadFile = File(...),
    authenticated: bool = Depends(security_manager.validate_service_token)
) -> ConvertResponse:
    """
    Convert uploaded file to Markdown (multipart/form-data).
    
    Args:
        file: Uploaded file (PDF, DOCX, DOC, or TXT)
        authenticated: Service token validation (injected by dependency)
        
    Returns:
        ConvertResponse with markdown content
    """
    start_time = time.time()
    temp_file = None
    
    try:
        # Read file content
        content = await file.read()
        
        # Store file temporarily
        temp_file = await file_manager.store_upload(content, file.filename)
        
        # Convert to markdown
        success, markdown, error = await marker_client.convert_to_markdown(temp_file)
        
        processing_time = time.time() - start_time
        
        if not success:
            return ConvertResponse(
                success=False,
                markdown_content=None,
                processing_time=processing_time,
                output_method=OutputMethod.INLINE,
                file_info={
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": len(content)
                },
                error=error or "Conversion failed"
            )
        
        return ConvertResponse(
            success=True,
            markdown_content=markdown,
            processing_time=processing_time,
            output_method=OutputMethod.INLINE,
            content_size=len(markdown.encode('utf-8')) if markdown else 0,
            file_info={
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content)
            }
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error("Conversion failed", error=str(e))
        return ConvertResponse(
            success=False,
            markdown_content=None,
            processing_time=processing_time,
            output_method=OutputMethod.INLINE,
            file_info={
                "filename": getattr(file, 'filename', 'unknown'),
                "content_type": getattr(file, 'content_type', 'unknown')
            },
            error=str(e)
        )
    finally:
        # Cleanup
        if temp_file:
            await file_manager.cleanup_file_async(temp_file)


@app.post("/v1/convert-json", response_model=ConvertResponse)
async def convert_file_json(
    request: ConvertRequest,
    authenticated: bool = Depends(security_manager.validate_service_token)
) -> ConvertResponse:
    """
    Convert file to Markdown (JSON request for orchestrator).
    
    Args:
        request: Conversion request with file content or URL
        authenticated: Service token validation (injected by dependency)
        
    Returns:
        ConvertResponse with markdown content or reference
    """
    start_time = time.time()
    temp_file = None
    
    try:
        # Process input (base64 or URL)
        temp_file, file_metadata = await file_manager.process_input(
            file_content=request.file_content,
            file_url=request.file_url,
            filename=request.filename
        )
        
        # Convert to markdown
        success, markdown, error = await marker_client.convert_to_markdown(temp_file)
        
        processing_time = time.time() - start_time
        
        if not success:
            return ConvertResponse(
                success=False,
                markdown_content=None,
                processing_time=processing_time,
                output_method=OutputMethod.INLINE,
                request_id=request.request_id,
                file_info={
                    "filename": request.filename,
                    "content_type": request.content_type,
                    **file_metadata
                },
                error=error or "Conversion failed"
            )
        
        # Handle output based on method
        actual_method, inline_content, reference_url = await file_manager.store_output(
            content=markdown,
            filename=request.filename,
            output_method=request.output_method,
            max_inline_size=request.max_inline_size
        )
        
        return ConvertResponse(
            success=True,
            markdown_content=inline_content,
            markdown_url=reference_url,
            content_size=len(markdown.encode('utf-8')),
            processing_time=processing_time,
            output_method=actual_method,
            request_id=request.request_id,
            file_info={
                "filename": request.filename,
                "content_type": request.content_type,
                **file_metadata
            }
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error("JSON conversion failed", error=str(e))
        return ConvertResponse(
            success=False,
            markdown_content=None,
            processing_time=processing_time,
            output_method=OutputMethod.INLINE,
            request_id=request.request_id,
            file_info={
                "filename": request.filename,
                "content_type": request.content_type
            },
            error=str(e)
        )
    finally:
        # Cleanup
        if temp_file:
            await file_manager.cleanup_file_async(temp_file)


@app.get("/outputs/{filename}")
async def get_output_file(
    filename: str,
    authenticated: bool = Depends(security_manager.validate_service_token)
):
    """
    Retrieve stored output file.
    
    Args:
        filename: Name of the output file
        authenticated: Service token validation
        
    Returns:
        File content
    """
    try:
        output_path = file_manager.output_dir / filename
        
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Security check - ensure file is in output directory
        if not str(output_path).startswith(str(file_manager.output_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {"content": content, "filename": filename}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve output file {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug")
async def debug_info():
    """Debug endpoint without authentication."""
    return {
        "message": "Debug endpoint working",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "settings_loaded": bool(settings),
        "security_manager_loaded": bool(security_manager)
    }

@app.get("/system/info")
async def get_system_info(
    authenticated: bool = Depends(security_manager.validate_service_token)
):
    """Get system information for monitoring."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "uptime": "system_uptime",  # Could implement actual uptime tracking
        "file_system": file_manager.get_temp_dir_info(),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
