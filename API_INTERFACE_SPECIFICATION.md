# Markdown Service API Interface Specification

**Version**: 1.0.0  
**Service**: markdown-service  
**Port**: 8002  
**Base URL**: `http://markdown-service:8002`

## 📋 Overview

Markdown Service provides high-performance document conversion from multiple formats (PDF, DOCX, DOC, TXT) to Markdown. This document defines the complete interface contract for integration with orchestrator and other microservices.

## 🏗️ Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orchestrator  │    │  Marker API     │    │ Markdown Service│
│                 │    │   (External)    │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Task Queue   │ │    │ │Document     │ │    │ │File         │ │
│ │Management   │ │───▶│ │Processing   │ │◀───│ │Conversion   │ │
│ └─────────────┘ │    │ │Service      │ │    │ │Engine       │ │
└─────────────────┘    │ └─────────────┘ │    │ └─────────────┘ │
                       └─────────────────┘    │ ┌─────────────┐ │
                                              │ │File         │ │
                                              │ │Management   │ │
                                              │ └─────────────┘ │
                                              └─────────────────┘
```

## 🔌 API Endpoints

### 1. Convert Document (File Upload)

**Endpoint**: `POST /v1/convert`  
**Content-Type**: `multipart/form-data`

**Description**: Convert uploaded document to Markdown format. Suitable for direct API calls.

#### Request
```http
POST /v1/convert
Content-Type: multipart/form-data
X-Service-Token: your-service-token

Form Data:
- file: [binary file content]
```

#### Response
```json
{
  "success": true,
  "markdown_content": "# Document Title\n\nDocument content in markdown...",
  "markdown_url": null,
  "content_size": 2048,
  "processing_time": 15.75,
  "output_method": "inline",
  "request_id": null,
  "file_info": {
    "filename": "document.pdf",
    "content_type": "application/pdf",
    "size": 1048576
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. Convert Document (JSON - Orchestrator)

**Endpoint**: `POST /v1/convert-json`  
**Content-Type**: `application/json`

**Description**: Convert document using JSON request. Optimized for orchestrator integration with flexible input/output methods.

#### Base64 Content Request
```json
{
  "file_content": "JVBERi0xLjQ...",
  "filename": "document.pdf",
  "content_type": "application/pdf",
  "request_id": "orch_batch_001_item_042",
  "output_method": "auto",
  "max_inline_size": 1048576,
  "priority": 1,
  "callback_url": "http://orchestrator:8000/callbacks/markdown"
}
```

#### URL Reference Request
```json
{
  "file_url": "s3://bucket/documents/resume.pdf",
  "filename": "resume.pdf",
  "content_type": "application/pdf",
  "request_id": "orch_batch_001_item_043",
  "output_method": "reference",
  "priority": 1
}
```

#### Response (Inline Content)
```json
{
  "success": true,
  "markdown_content": "# Resume\n\n## Professional Experience\n...",
  "markdown_url": null,
  "content_size": 2048,
  "processing_time": 12.34,
  "output_method": "inline",
  "request_id": "orch_batch_001_item_042",
  "file_info": {
    "filename": "document.pdf",
    "content_type": "application/pdf",
    "size": 1048576,
    "source": "base64",
    "checksum": "d41d8cd98f00b204e9800998ecf8427e"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Response (Reference Content)
```json
{
  "success": true,
  "markdown_content": null,
  "markdown_url": "/outputs/doc_abc123def456.md",
  "content_size": 5242880,
  "processing_time": 45.67,
  "output_method": "reference",
  "request_id": "orch_batch_001_item_043",
  "file_info": {
    "filename": "large_document.pdf",
    "content_type": "application/pdf",
    "size": 10485760,
    "source": "url",
    "source_url": "s3://bucket/documents/resume.pdf",
    "checksum": "098f6bcd4621d373cade4e832627b4f6"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. Get Output File

**Endpoint**: `GET /outputs/{filename}`

**Description**: Retrieve stored output file content for reference-mode conversions.

#### Request
```http
GET /outputs/doc_abc123def456.md
X-Service-Token: your-service-token
```

#### Response
```json
{
  "content": "# Document Title\n\nDocument content...",
  "filename": "doc_abc123def456.md"
}
```

### 4. Health Check

**Endpoint**: `GET /health`

**Description**: Service health status with dependency checks.

#### Response
```json
{
  "status": "healthy",
  "service": "markdown-service",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "checks": {
    "service_status": true,
    "temp_directory": true,
    "marker_api_configured": true
  }
}
```

### 5. System Information

**Endpoint**: `GET /system/info`

**Description**: System resource information and file management status.

#### Response
```json
{
  "service": "markdown-service",
  "version": "1.0.0",
  "uptime": "system_uptime",
  "file_system": {
    "temp_dir": "/tmp/markdown-service",
    "output_dir": "/tmp/markdown-service/outputs",
    "temp_file_count": 3,
    "output_file_count": 15,
    "total_size_mb": 45.2,
    "free_space_mb": 2048.0,
    "total_space_mb": 4096.0,
    "usage_percent": 50.0
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 6. Metrics

**Endpoint**: `GET /metrics`

**Description**: Prometheus-format metrics for monitoring.

#### Response (Prometheus Format)
```
# HELP markdown_requests_total Total number of conversion requests
# TYPE markdown_requests_total counter
markdown_requests_total{method="POST",endpoint="/v1/convert"} 1234

# HELP markdown_processing_time_seconds Time spent processing conversions
# TYPE markdown_processing_time_seconds histogram
markdown_processing_time_seconds_bucket{le="1.0"} 45
markdown_processing_time_seconds_bucket{le="5.0"} 123
markdown_processing_time_seconds_bucket{le="10.0"} 200
```

## 📊 Request/Response Models

### ConvertRequest (JSON Endpoint)
```typescript
interface ConvertRequest {
  // Input options (one required)
  file_content?: string;     // Base64 encoded file content
  file_url?: string;         // URL to download file from
  
  // Required fields
  filename: string;          // Original filename with extension
  
  // Optional fields
  content_type?: string;     // MIME type (auto-detected if not provided)
  request_id?: string;       // Orchestrator request ID for tracking
  output_method?: "inline" | "reference" | "auto";  // Default: "auto"
  max_inline_size?: number;  // Max size for inline content (default: 1MB)
  priority?: number;         // Processing priority 1-10 (default: 5)
  callback_url?: string;     // Callback URL for async processing
}
```

### ConvertResponse
```typescript
interface ConvertResponse {
  success: boolean;
  
  // Content options
  markdown_content?: string; // Converted content (if inline)
  markdown_url?: string;     // URL to content file (if reference)
  content_size?: number;     // Size of converted content in bytes
  
  // Metadata
  request_id?: string;       // Request ID for tracking
  processing_time: number;   // Processing time in seconds
  output_method: "inline" | "reference";
  
  // File information
  file_info: {
    filename: string;
    content_type: string;
    size: number;
    source?: "upload" | "base64" | "url";
    source_url?: string;     // Original URL if from URL
    checksum?: string;       // MD5 checksum
  };
  
  // Error handling
  error?: string;            // Error message if failed
  error_code?: string;       // Machine-readable error code
  timestamp: string;         // ISO 8601 timestamp
}
```

### HealthCheck
```typescript
interface HealthCheck {
  status: "healthy" | "unhealthy" | "degraded";
  service: string;
  version: string;
  timestamp: string;
  checks: {
    service_status: boolean;
    temp_directory: boolean;
    marker_api_configured: boolean;
  };
}
```

## 🔧 Configuration Parameters

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MARKER_API_KEY` | string | **required** | Marker API authentication key |
| `MARKER_API_URL` | string | `https://www.datalab.to/api/v1/marker` | Marker API endpoint |
| `SERVICE_TOKEN` | string | `dev-token` | Service authentication token |
| `DEV_MODE` | boolean | `true` | Enable development mode |
| `PORT` | integer | `8002` | Service port |
| `HOST` | string | `0.0.0.0` | Service host |
| `TEMP_DIR` | string | `/tmp/markdown-service` | Temporary files directory |
| `MAX_FILE_SIZE` | integer | `52428800` | Maximum file size (50MB) |
| `MAX_INLINE_SIZE` | integer | `1048576` | Maximum inline content size (1MB) |
| `REQUEST_TIMEOUT` | integer | `300` | API request timeout (seconds) |
| `RETRY_ATTEMPTS` | integer | `3` | Number of retry attempts |
| `RETRY_DELAY` | float | `1.0` | Base delay between retries |
| `POLL_INTERVAL` | integer | `2` | Polling interval (seconds) |
| `MAX_POLLS` | integer | `300` | Maximum polling attempts |
| `LOG_LEVEL` | string | `INFO` | Logging level |
| `LOG_FORMAT` | string | `json` | Log format (json/console) |

### Supported File Formats

| Format | Extensions | MIME Types |
|--------|------------|------------|
| PDF | `.pdf` | `application/pdf` |
| Word | `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| Word Legacy | `.doc` | `application/msword` |
| Text | `.txt` | `text/plain` |

### Output Methods

| Method | Description | When Used |
|--------|-------------|-----------|
| `inline` | Return content directly in response | Small files, immediate access needed |
| `reference` | Store file and return URL reference | Large files, memory optimization |
| `auto` | Automatically choose based on content size | Default behavior, size < max_inline_size |

## 🚨 Error Handling

### Error Response Format
All errors return a consistent ConvertResponse with `success: false`:

```json
{
  "success": false,
  "markdown_content": null,
  "markdown_url": null,
  "processing_time": 2.5,
  "output_method": "inline",
  "request_id": "orch_batch_001_item_042",
  "file_info": {
    "filename": "document.pdf",
    "content_type": "application/pdf"
  },
  "error": "File too large: 104857600 bytes",
  "error_code": "FILE_TOO_LARGE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Codes

| Code | HTTP Status | Description | Solution |
|------|-------------|-------------|----------|
| `INVALID_FILE_FORMAT` | 400 | Unsupported file type | Use supported formats (PDF, DOCX, DOC, TXT) |
| `FILE_TOO_LARGE` | 400 | File exceeds size limit | Reduce file size or increase limit |
| `INVALID_BASE64` | 400 | Malformed base64 content | Verify base64 encoding |
| `INVALID_URL` | 400 | Invalid or inaccessible URL | Check URL format and accessibility |
| `MISSING_FILE_INPUT` | 400 | No file content or URL provided | Provide either file_content or file_url |
| `MARKER_API_ERROR` | 500 | External API failure | Check Marker API status, retry |
| `PROCESSING_TIMEOUT` | 504 | Conversion took too long | Retry with smaller file or increase timeout |
| `STORAGE_ERROR` | 500 | File storage failure | Check disk space and permissions |
| `AUTHENTICATION_ERROR` | 401 | Invalid service token | Verify X-Service-Token header |

### Retry Strategy

The service implements automatic retry for transient failures:

- **Attempts**: 3 retries with exponential backoff
- **Delay**: 1s, 2s, 4s between attempts  
- **Conditions**: Network errors, temporary API failures, rate limiting
- **Final Failure**: Returns error response after all retries exhausted

## 🔐 Authentication

### Service Token Authentication

All endpoints require authentication via the `X-Service-Token` header:

```http
X-Service-Token: your-service-token
```

### Development Mode
- Default token: `dev-token`
- No external validation required
- Suitable for testing and development

### Production Mode
- Custom service token via `SERVICE_TOKEN` environment variable
- Validated by security manager
- Required for production deployments

## 📈 Performance Characteristics

### Processing Times (Typical)
- **Text files**: 1-3 seconds
- **PDF files**: 5-30 seconds (depends on size and complexity)
- **Word documents**: 3-15 seconds
- **Large files (>10MB)**: 30-120 seconds

### Throughput
- **Concurrent requests**: Limited by Marker API rate limits
- **File size optimization**: Automatic based on content
- **Memory usage**: Minimized through streaming and cleanup

### Rate Limiting
- Inherits Marker API rate limits
- Automatic retry with backoff
- Queue management for high-volume scenarios

## 🔄 Integration Patterns

### Orchestrator Integration
```python
# Example orchestrator task submission
task = {
    "service": "markdown-service",
    "operation": "convert-json", 
    "payload": {
        "file_content": base64_content,
        "filename": "resume.pdf",
        "request_id": "batch_001_item_042",
        "output_method": "auto",
        "priority": 1
    },
    "timeout": 300
}
```

### Chaining with Other Services
```python
# Markdown → JSON Service Chain
markdown_response = markdown_service.convert(file)
if markdown_response["success"]:
    if markdown_response["output_method"] == "inline":
        content = markdown_response["markdown_content"]
    else:
        content = markdown_service.get_output(markdown_response["markdown_url"])
    
    # Pass to JSON service
    json_response = json_service.convert(content)
```

### Batch Processing
```python
# Process multiple files
for file_data in batch_files:
    task = {
        "file_content": file_data["content"],
        "filename": file_data["name"],
        "request_id": f"batch_{batch_id}_item_{file_data['id']}",
        "output_method": "reference",  # Use references for batch
        "priority": 5
    }
    submit_to_queue(task)
```

## 📊 Monitoring and Observability

### Health Check Interpretation
- `healthy`: All systems operational
- `degraded`: Some non-critical issues (e.g., high disk usage)
- `unhealthy`: Critical failures (e.g., API key missing, temp directory inaccessible)

### Key Metrics to Monitor
- Request rate and success rate
- Processing times (p50, p95, p99)
- File system usage
- Error rates by type
- Marker API response times

### Logging
- Structured JSON logging
- Request tracing with request_id
- Performance metrics per request
- Error details with stack traces

---

**Last Updated**: 2024-01-15  
**API Version**: 1.0.0  
**Document Version**: 1.0.0 