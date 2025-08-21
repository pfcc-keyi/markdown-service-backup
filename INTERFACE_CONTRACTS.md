# Markdown Service Interface Contracts

**Version**: 1.0.0  
**Service**: markdown-service  
**Purpose**: Formal service contracts and data schemas for integration teams

## 📋 Overview

This document defines the formal contracts, data schemas, and interface specifications for the Markdown Service. Use this as the authoritative reference for integration development.

## 🔌 Service Endpoints Contract

### Base Service Information
```yaml
service_name: markdown-service
service_version: 1.0.0
base_url: http://markdown-service:8002
authentication: X-Service-Token header required
content_types: 
  - application/json
  - multipart/form-data
```

### Endpoint Registry
| Endpoint | Method | Purpose | Input | Output |
|----------|--------|---------|-------|--------|
| `/v1/convert` | POST | File upload conversion | multipart/form-data | ConvertResponse |
| `/v1/convert-json` | POST | JSON-based conversion | ConvertRequest | ConvertResponse |
| `/outputs/{filename}` | GET | Retrieve reference content | Path parameter | FileContent |
| `/health` | GET | Service health check | None | HealthCheck |
| `/system/info` | GET | System information | None | SystemInfo |
| `/metrics` | GET | Prometheus metrics | None | Metrics (text/plain) |

## 📊 Data Schemas

### ConvertRequest Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "ConvertRequest",
  "description": "Request schema for document conversion",
  "properties": {
    "file_content": {
      "type": "string",
      "description": "Base64 encoded file content",
      "format": "base64"
    },
    "file_url": {
      "type": "string",
      "description": "URL to download file from",
      "format": "uri"
    },
    "filename": {
      "type": "string",
      "description": "Original filename with extension",
      "pattern": "^.+\\.(pdf|docx|doc|txt)$",
      "maxLength": 255
    },
    "content_type": {
      "type": "string",
      "description": "MIME type of the file",
      "enum": [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
      ]
    },
    "request_id": {
      "type": "string",
      "description": "Orchestrator request ID for tracking",
      "maxLength": 100
    },
    "output_method": {
      "type": "string",
      "description": "How to return results",
      "enum": ["inline", "reference", "auto"],
      "default": "auto"
    },
    "max_inline_size": {
      "type": "integer",
      "description": "Maximum size for inline content in bytes",
      "minimum": 1024,
      "maximum": 10485760,
      "default": 1048576
    },
    "priority": {
      "type": "integer",
      "description": "Processing priority (1=highest, 10=lowest)",
      "minimum": 1,
      "maximum": 10,
      "default": 5
    },
    "callback_url": {
      "type": "string",
      "description": "Callback URL for async processing",
      "format": "uri"
    }
  },
  "required": ["filename"],
  "oneOf": [
    {"required": ["file_content"]},
    {"required": ["file_url"]}
  ],
  "additionalProperties": false
}
```

### ConvertResponse Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "ConvertResponse",
  "description": "Response schema for document conversion",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the conversion was successful"
    },
    "markdown_content": {
      "type": ["string", "null"],
      "description": "Converted markdown content (if inline)"
    },
    "markdown_url": {
      "type": ["string", "null"],
      "description": "URL to markdown file (if reference)",
      "pattern": "^/outputs/[a-zA-Z0-9_-]+\\.md$"
    },
    "content_size": {
      "type": ["integer", "null"],
      "description": "Size of converted content in bytes",
      "minimum": 0
    },
    "processing_time": {
      "type": "number",
      "description": "Processing time in seconds",
      "minimum": 0
    },
    "output_method": {
      "type": "string",
      "description": "How results were returned",
      "enum": ["inline", "reference"]
    },
    "request_id": {
      "type": ["string", "null"],
      "description": "Request ID for tracking"
    },
    "file_info": {
      "type": "object",
      "description": "File metadata",
      "properties": {
        "filename": {
          "type": "string",
          "description": "Original filename"
        },
        "content_type": {
          "type": "string",
          "description": "MIME type"
        },
        "size": {
          "type": "integer",
          "description": "File size in bytes",
          "minimum": 0
        },
        "source": {
          "type": "string",
          "description": "Input source method",
          "enum": ["upload", "base64", "url"]
        },
        "source_url": {
          "type": "string",
          "description": "Original URL if from URL source"
        },
        "checksum": {
          "type": "string",
          "description": "MD5 checksum",
          "pattern": "^[a-f0-9]{32}$"
        }
      },
      "required": ["filename", "content_type", "size"],
      "additionalProperties": false
    },
    "error": {
      "type": ["string", "null"],
      "description": "Error message if conversion failed"
    },
    "error_code": {
      "type": ["string", "null"],
      "description": "Machine-readable error code",
      "enum": [
        "INVALID_FILE_FORMAT",
        "FILE_TOO_LARGE",
        "INVALID_BASE64",
        "INVALID_URL",
        "MISSING_FILE_INPUT",
        "MARKER_API_ERROR",
        "PROCESSING_TIMEOUT",
        "STORAGE_ERROR",
        "AUTHENTICATION_ERROR"
      ]
    },
    "timestamp": {
      "type": "string",
      "description": "ISO 8601 timestamp",
      "format": "date-time"
    }
  },
  "required": ["success", "processing_time", "output_method", "file_info", "timestamp"],
  "additionalProperties": false
}
```

### HealthCheck Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "HealthCheck",
  "description": "Health check response schema",
  "properties": {
    "status": {
      "type": "string",
      "description": "Overall health status",
      "enum": ["healthy", "unhealthy", "degraded"]
    },
    "service": {
      "type": "string",
      "description": "Service name",
      "const": "markdown-service"
    },
    "version": {
      "type": "string",
      "description": "Service version",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "timestamp": {
      "type": "string",
      "description": "Health check timestamp",
      "format": "date-time"
    },
    "checks": {
      "type": "object",
      "description": "Individual health checks",
      "properties": {
        "service_status": {
          "type": "boolean",
          "description": "Service is running"
        },
        "temp_directory": {
          "type": "boolean",
          "description": "Temp directory is writable"
        },
        "marker_api_configured": {
          "type": "boolean",
          "description": "Marker API key is configured"
        }
      },
      "required": ["service_status", "temp_directory", "marker_api_configured"],
      "additionalProperties": true
    }
  },
  "required": ["status", "service", "version", "timestamp", "checks"],
  "additionalProperties": false
}
```

### SystemInfo Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "SystemInfo",
  "description": "System information response schema",
  "properties": {
    "service": {
      "type": "string",
      "const": "markdown-service"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "uptime": {
      "type": "string",
      "description": "Service uptime information"
    },
    "file_system": {
      "type": "object",
      "description": "File system usage information",
      "properties": {
        "temp_dir": {
          "type": "string",
          "description": "Temporary directory path"
        },
        "output_dir": {
          "type": "string",
          "description": "Output directory path"
        },
        "temp_file_count": {
          "type": "integer",
          "description": "Number of temporary files",
          "minimum": 0
        },
        "output_file_count": {
          "type": "integer",
          "description": "Number of output files",
          "minimum": 0
        },
        "total_size_mb": {
          "type": "number",
          "description": "Total size in MB",
          "minimum": 0
        },
        "free_space_mb": {
          "type": "number",
          "description": "Free space in MB",
          "minimum": 0
        },
        "total_space_mb": {
          "type": "number",
          "description": "Total space in MB",
          "minimum": 0
        },
        "usage_percent": {
          "type": "number",
          "description": "Usage percentage",
          "minimum": 0,
          "maximum": 100
        }
      },
      "required": [
        "temp_dir", "output_dir", "temp_file_count", "output_file_count",
        "total_size_mb", "free_space_mb", "total_space_mb", "usage_percent"
      ],
      "additionalProperties": false
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["service", "version", "file_system", "timestamp"],
  "additionalProperties": false
}
```

### FileContent Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "FileContent",
  "description": "Output file content response schema",
  "properties": {
    "content": {
      "type": "string",
      "description": "File content as string"
    },
    "filename": {
      "type": "string",
      "description": "Filename",
      "pattern": "^[a-zA-Z0-9_-]+\\.md$"
    }
  },
  "required": ["content", "filename"],
  "additionalProperties": false
}
```

## 🔗 Service Dependencies

### External Dependencies
| Service | Type | Purpose | Contract |
|---------|------|---------|----------|
| Marker API | External HTTP | Document processing | https://www.datalab.to/api/v1/marker |

### Internal Dependencies
| Component | Type | Purpose |
|-----------|------|---------|
| File System | Local | Temporary file storage |
| Temp Directory | Local | Input file processing |
| Output Directory | Local | Reference file storage |

## 🚨 Error Contracts

### Error Response Format
All endpoints return errors in the same ConvertResponse format with `success: false`:

```typescript
interface ErrorResponse {
  success: false;
  markdown_content: null;
  markdown_url: null;
  processing_time: number;
  output_method: "inline" | "reference";
  request_id?: string;
  file_info: FileInfo;
  error: string;           // Human-readable error message
  error_code: ErrorCode;   // Machine-readable error code
  timestamp: string;       // ISO 8601 timestamp
}
```

### Error Code Definitions
| Code | HTTP Status | Retry | Description |
|------|-------------|-------|-------------|
| `INVALID_FILE_FORMAT` | 400 | No | Unsupported file type |
| `FILE_TOO_LARGE` | 400 | No | File exceeds size limit |
| `INVALID_BASE64` | 400 | No | Malformed base64 content |
| `INVALID_URL` | 400 | No | Invalid or inaccessible URL |
| `MISSING_FILE_INPUT` | 400 | No | No file content or URL provided |
| `MARKER_API_ERROR` | 500 | Yes | External API failure |
| `PROCESSING_TIMEOUT` | 504 | Yes | Conversion took too long |
| `STORAGE_ERROR` | 500 | Yes | File storage failure |
| `AUTHENTICATION_ERROR` | 401 | No | Invalid service token |

## 🔐 Authentication Contract

### Service Token Authentication
```http
X-Service-Token: {token}
```

#### Development Mode
- Default token: `dev-token`
- No external validation
- Suitable for testing only

#### Production Mode
- Custom token via `SERVICE_TOKEN` environment variable
- Validated by security manager
- Required for production deployments

### Authentication Errors
```json
{
  "success": false,
  "error": "Invalid or missing service token",
  "error_code": "AUTHENTICATION_ERROR",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 📈 Performance Contracts

### SLA Commitments
| Metric | Target | Measurement |
|--------|--------|-------------|
| Availability | 99.9% | Monthly uptime |
| Response Time (p95) | < 30s | End-to-end processing |
| Response Time (p99) | < 60s | End-to-end processing |
| Throughput | 10 req/min | Sustained load |
| Error Rate | < 1% | Failed requests |

### File Size Limits
| Format | Maximum Size | Processing Time |
|--------|-------------|-----------------|
| Text (.txt) | 10MB | 1-5 seconds |
| PDF (.pdf) | 50MB | 5-60 seconds |
| Word (.docx) | 50MB | 3-30 seconds |
| Word Legacy (.doc) | 50MB | 5-45 seconds |

### Output Size Thresholds
| Method | Condition | Behavior |
|--------|-----------|----------|
| Inline | Content < max_inline_size | Return in response |
| Reference | Content >= max_inline_size | Store and return URL |
| Auto | Based on max_inline_size | Automatic selection |

## 🔄 Orchestrator Integration Contract

### Task Submission Format
```json
{
  "service": "markdown-service",
  "operation": "convert-json",
  "payload": {
    "file_content": "base64_content",
    "filename": "document.pdf",
    "request_id": "batch_001_item_042",
    "output_method": "auto",
    "priority": 1
  },
  "timeout": 300,
  "retry_attempts": 3
}
```

### Response Handling
```python
def handle_response(response):
    if response["success"]:
        if response["output_method"] == "inline":
            content = response["markdown_content"]
        else:
            # Fetch from reference
            content = fetch_output_file(response["markdown_url"])
        return content
    else:
        handle_error(response["error_code"], response["error"])
```

### Service Chaining Contract
```yaml
chain_definition:
  - service: markdown-service
    operation: convert-json
    output: markdown_content
  - service: json-service
    operation: convert
    input: markdown_content
    output: structured_data
```

## 📊 Monitoring Contracts

### Health Check Contract
- **Endpoint**: `GET /health`
- **Frequency**: Every 30 seconds
- **Timeout**: 10 seconds
- **Expected Response Time**: < 1 second

### Metrics Contract (Prometheus)
```
# Request metrics
markdown_requests_total{method, endpoint, status}
markdown_request_duration_seconds{method, endpoint}

# Processing metrics  
markdown_processing_time_seconds{file_type}
markdown_file_size_bytes{file_type}

# System metrics
markdown_temp_files_total
markdown_output_files_total
markdown_disk_usage_bytes{type}

# Error metrics
markdown_errors_total{error_code}
markdown_marker_api_errors_total{type}
```

### Logging Contract
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "markdown-service",
  "request_id": "req_123",
  "endpoint": "/v1/convert-json",
  "processing_time": 12.34,
  "file_size": 1048576,
  "output_method": "inline",
  "message": "Conversion completed successfully"
}
```

## 🧪 Testing Contracts

### Unit Test Coverage
- **Minimum Coverage**: 80%
- **Critical Paths**: 95%
- **Test Categories**: Unit, Integration, E2E

### Integration Test Requirements
```python
def test_integration_contract():
    """Verify service adheres to interface contracts"""
    # Test successful conversion
    response = call_convert_api(test_data)
    assert_response_schema(response, ConvertResponse)
    
    # Test error handling
    error_response = call_convert_api(invalid_data)
    assert_error_contract(error_response)
    
    # Test health check
    health = call_health_api()
    assert_health_schema(health, HealthCheck)
```

### Load Test Requirements
```yaml
load_test_scenarios:
  - name: normal_load
    rps: 5
    duration: 5m
    file_size: 1MB
    
  - name: peak_load
    rps: 10
    duration: 2m
    file_size: 5MB
    
  - name: stress_test
    rps: 20
    duration: 1m
    file_size: 10MB
```

## 📋 Versioning Contract

### API Versioning
- **Current Version**: v1
- **URL Pattern**: `/v{version}/{endpoint}`
- **Backward Compatibility**: 2 major versions
- **Deprecation Notice**: 3 months minimum

### Schema Evolution
```yaml
compatibility_rules:
  - new_optional_fields: allowed
  - field_removal: requires_major_version
  - field_type_changes: requires_major_version
  - enum_value_addition: allowed
  - enum_value_removal: requires_major_version
```

### Breaking Changes
Major version increments required for:
- Required field removal
- Field type changes
- Enum value removal
- HTTP status code changes
- Error code changes

---

**Document Version**: 1.0.0  
**Service Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**Contract Authority**: Markdown Service Team 