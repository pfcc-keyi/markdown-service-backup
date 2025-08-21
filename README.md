# Markdown Service

A professional microservice for converting documents to Markdown format using the Marker API, designed for seamless orchestrator integration.

## 🏗️ Architecture Overview

This service provides high-performance document conversion capabilities:
- **Multi-format Support**: PDF, DOCX, DOC, TXT to Markdown conversion
- **Flexible Input/Output**: File upload, Base64, URL input with inline/reference output
- **Orchestrator Integration**: Optimized for microservice orchestration
- **File Management**: Intelligent temporary file handling and cleanup
- **Production Ready**: Docker support, health monitoring, and observability

## 🚀 Features

- **High Performance**: FastAPI-based async API with concurrent processing
- **Multiple Input Methods**: File upload, Base64 content, URL references
- **Smart Output Strategy**: Automatic inline/reference decision based on content size
- **File Lifecycle Management**: Secure temporary file handling with automatic cleanup
- **Marker API Integration**: Professional document processing with retry logic
- **Health Monitoring**: Comprehensive health checks and system metrics
- **Security**: Service token authentication and file access controls

## 📋 API Endpoints

### Convert Document (Upload)
```http
POST /v1/convert
Content-Type: multipart/form-data

curl -X POST "http://localhost:8002/v1/convert" \
  -H "X-Service-Token: dev-token" \
  -F "file=@document.pdf"
```

### Convert Document (JSON - Orchestrator)
```http
POST /v1/convert-json
Content-Type: application/json

{
  "file_content": "JVBERi0xLjQ...",  // base64 encoded
  "filename": "document.pdf",
  "request_id": "orch_12345",
  "output_method": "auto",
  "max_inline_size": 1048576,
  "priority": 1
}
```

### Get Output File
```http
GET /outputs/{filename}
Authorization: X-Service-Token: your-token
```

### Health Check
```http
GET /health
```

### System Information
```http
GET /system/info
```

### Metrics
```http
GET /metrics
```

## 🔧 Configuration

### Development Mode Variables
- `DEV_MODE`: Enable development mode (default: true)
- `MARKER_API_KEY`: Your Marker API key (required)
- `LOG_LEVEL`: Logging level (default: INFO, suggested: DEBUG for dev)
- `LOG_FORMAT`: Log format (default: json, suggested: console for dev)

### Production Mode Variables
- `SERVICE_TOKEN`: Authentication token for inter-service communication
- `MARKER_API_URL`: Marker API endpoint (default: https://www.datalab.to/api/v1/marker)
- `REQUEST_TIMEOUT`: API request timeout in seconds (default: 300)
- `RETRY_ATTEMPTS`: Number of retry attempts (default: 3)

### File Management Variables
- `TEMP_DIR`: Temporary files directory (default: /tmp/markdown-service)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 52428800 = 50MB)
- `MAX_INLINE_SIZE`: Maximum size for inline content (default: 1048576 = 1MB)

### Common Variables
- `PORT`: Service port (default: 8002)
- `HOST`: Service host (default: 0.0.0.0)

## 🏃‍♂️ Quick Start

### Development Mode 🧪

Perfect for testing and development:

```bash
cd markdown-service

# Create and activate virtual environment
python -m venv markdown-env
source markdown-env/bin/activate  # Linux/Mac
# or markdown-env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set your Marker API key
export MARKER_API_KEY=your-marker-api-key-here

# Option 1: Interactive startup (recommended)
python dev_start.py

# Option 2: Manual environment setup
export DEV_MODE=true
python -m src.markdown_service.main
```

**Development Mode Features:**
- ✅ Simple service token authentication (dev-token)
- ✅ Uses your direct Marker API key
- ✅ Console logging for easy debugging
- ✅ All endpoints work normally
- ✅ File cleanup and monitoring

**Test the service:**
```bash
# Health check
curl http://localhost:8002/health

# Test file upload conversion
curl -X POST "http://localhost:8002/v1/convert" \
  -H "X-Service-Token: dev-token" \
  -F "file=@tests/test_files/test.pdf"

# Test JSON conversion (orchestrator style)
curl -X POST "http://localhost:8002/v1/convert-json" \
  -H "Content-Type: application/json" \
  -H "X-Service-Token: dev-token" \
  -d '{
    "file_content": "'$(base64 tests/test_files/test.pdf)'",
    "filename": "test.pdf",
    "request_id": "test-001",
    "output_method": "auto"
  }'

# Check system info
curl -H "X-Service-Token: dev-token" \
  http://localhost:8002/system/info
```

### Production Mode (With Orchestrator)

For the full microservice ecosystem:

```bash
cd markdown-service
pip install -r requirements.txt

# Set production environment variables
export MARKER_API_KEY=your-marker-api-key
export SERVICE_TOKEN=your-service-token
export DEV_MODE=false

python -m src.markdown_service.main
```

### Docker Deployment
```bash
docker build -t markdown-service .
docker run -p 8002:8002 \
  -e MARKER_API_KEY=your-key \
  -e SERVICE_TOKEN=your-token \
  markdown-service
```

## 📊 Monitoring

- Health endpoint: `/health` - Service health status
- System info: `/system/info` - File system and resource usage
- Metrics endpoint: `/metrics` - Prometheus format metrics
- Structured JSON logging with request tracking

## 🔗 Dependencies

- **Marker API**: External document processing service
- **File System**: For temporary file storage and output management
- **httpx**: For async HTTP requests to Marker API

## 🧪 Testing

```bash
# Install test dependencies
pip install -r requirements.txt

# Unit tests
pytest tests/unit/ -v

# Integration tests  
pytest tests/integration/ -v

# Test with actual files
python tests/test_conversion.py
```

## 🎯 Output Strategies

### Inline Output (Small Files)
```json
{
  "success": true,
  "markdown_content": "# Document Title\n\nContent...",
  "markdown_url": null,
  "content_size": 1024,
  "output_method": "inline"
}
```

### Reference Output (Large Files)
```json
{
  "success": true,
  "markdown_content": null,
  "markdown_url": "/outputs/doc_abc123.md",
  "content_size": 5242880,
  "output_method": "reference"
}
```

### Auto Selection
- Files < 1MB: Inline return
- Files >= 1MB: Reference return

## 🔄 File Lifecycle

```
1. Input Processing
   ├── File upload / Base64 decode / URL download
   ├── Store to temporary directory
   └── Generate file metadata

2. Conversion
   ├── Submit to Marker API
   ├── Poll for completion
   └── Retrieve markdown content

3. Output Processing
   ├── Determine output method (inline/reference)
   ├── Store large files in output directory
   └── Return response with content or reference

4. Cleanup
   ├── Delete temporary input files
   └── Scheduled cleanup of old output files
```

## 🚨 Error Handling

All errors return consistent format:
```json
{
  "success": false,
  "markdown_content": null,
  "processing_time": 2.5,
  "error": "File too large: 104857600 bytes",
  "error_code": "FILE_TOO_LARGE",
  "request_id": "batch_001_item_042"
}
```

## 📖 Additional Documentation

- [API Interface Specification](API_INTERFACE_SPECIFICATION.md) - Complete API documentation
- [Integration Guide](INTEGRATION_GUIDE.md) - Quick reference for developers
- [Interface Contracts](INTERFACE_CONTRACTS.md) - Service contracts and schemas
- [Orchestrator Integration](ORCHESTRATOR_INTEGRATION.md) - Orchestrator-specific guide
- [Development Guide](DEV_MODE_GUIDE.md) - Development setup and testing 