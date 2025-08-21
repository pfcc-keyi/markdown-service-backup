# 🧪 Markdown Service Development Mode Guide

> **Complete guide for development, testing, and debugging**

## 📋 Overview

Development mode provides a streamlined environment for testing the Markdown Service without complex infrastructure setup. Perfect for developers working on integration, testing new features, or debugging issues.

## 🚀 Quick Start (3 Steps)

### 1. Setup Environment
```bash
cd markdown-service

# Create virtual environment
python -m venv markdown-env
source markdown-env/bin/activate  # Linux/Mac
# or markdown-env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key
```bash
# Set your Marker API key
export MARKER_API_KEY=your-marker-api-key-here

# Optional: Set custom service token
export SERVICE_TOKEN=my-dev-token
```

### 3. Start Service
```bash
# Interactive startup (recommended)
python dev_start.py

# Manual startup
export DEV_MODE=true
python -m src.markdown_service.main
```

**Service will be available at: http://localhost:8002**

## 🔧 Development Mode Features

### ✅ What's Enabled
- **Simple Authentication**: Uses `dev-token` or custom token
- **Console Logging**: Easy-to-read colored output
- **Hot Reload**: Automatic restart on code changes
- **Debug Mode**: Detailed error messages and stack traces
- **API Documentation**: Swagger UI at `/docs` and ReDoc at `/redoc`
- **File Management**: Automatic temp file cleanup
- **Direct Marker API**: Uses your API key directly

### ❌ What's Disabled
- **External Dependencies**: No orchestrator required
- **Complex Authentication**: No external token validation
- **Production Logging**: JSON structured logging disabled
- **Rate Limiting**: Simplified for development

## 🔑 Environment Variables

### Required
```bash
MARKER_API_KEY=your-marker-api-key-here  # Get from DataLab
```

### Optional (Development)
```bash
DEV_MODE=true                    # Enable dev mode (default: true)
SERVICE_TOKEN=dev-token          # Auth token (default: dev-token)
PORT=8002                        # Service port (default: 8002)
HOST=0.0.0.0                     # Service host (default: 0.0.0.0)
LOG_LEVEL=DEBUG                  # Logging level (default: INFO)
LOG_FORMAT=console               # Log format (default: json, dev: console)
```

### File Management
```bash
TEMP_DIR=/tmp/markdown-service   # Temp files (default: /tmp/markdown-service)
MAX_FILE_SIZE=52428800          # Max file size 50MB (default: 52428800)
MAX_INLINE_SIZE=1048576         # Max inline size 1MB (default: 1048576)
```

### API Configuration
```bash
MARKER_API_URL=https://www.datalab.to/api/v1/marker  # Marker API endpoint
REQUEST_TIMEOUT=300             # API timeout seconds (default: 300)
RETRY_ATTEMPTS=3                # Retry attempts (default: 3)
RETRY_DELAY=1.0                 # Retry delay seconds (default: 1.0)
```

## 🧪 Testing the Service

### Health Check
```bash
curl http://localhost:8002/health
```

**Expected Response:**
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

### File Upload Test
```bash
# Test with a sample PDF
curl -X POST http://localhost:8002/v1/convert \
  -H "X-Service-Token: dev-token" \
  -F "file=@tests/test_files/test.pdf"
```

### JSON Conversion Test (Orchestrator Style)
```bash
# Convert file to base64 and test
base64_content=$(base64 tests/test_files/test.pdf | tr -d '\n')

curl -X POST http://localhost:8002/v1/convert-json \
  -H "Content-Type: application/json" \
  -H "X-Service-Token: dev-token" \
  -d '{
    "file_content": "'$base64_content'",
    "filename": "test.pdf",
    "request_id": "dev-test-001",
    "output_method": "auto"
  }'
```

### System Information
```bash
curl -H "X-Service-Token: dev-token" \
  http://localhost:8002/system/info
```

## 📊 API Documentation

### Swagger UI (Interactive)
- **URL**: http://localhost:8002/docs
- **Features**: Try endpoints directly, see request/response schemas
- **Authentication**: Use `dev-token` in the "Authorize" button

### ReDoc (Documentation)
- **URL**: http://localhost:8002/redoc
- **Features**: Comprehensive API documentation with examples

### OpenAPI Schema
- **URL**: http://localhost:8002/openapi.json
- **Features**: Machine-readable API specification

## 🔍 Debugging & Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check if port is in use
lsof -i :8002

# Check Python environment
which python
pip list | grep fastapi

# Check environment variables
echo $MARKER_API_KEY
echo $DEV_MODE
```

#### 2. Authentication Errors
```bash
# Test with correct header
curl -H "X-Service-Token: dev-token" http://localhost:8002/health

# If using custom token
curl -H "X-Service-Token: $SERVICE_TOKEN" http://localhost:8002/health
```

#### 3. File Conversion Errors
```bash
# Check file format
file tests/test_files/test.pdf

# Check file size
ls -lh tests/test_files/test.pdf

# Test with simple text file first
echo "Test content" > test.txt
curl -X POST http://localhost:8002/v1/convert \
  -H "X-Service-Token: dev-token" \
  -F "file=@test.txt"
```

#### 4. Marker API Issues
```bash
# Test API key manually
curl -X GET https://www.datalab.to/api/v1/marker/health \
  -H "X-Api-Key: $MARKER_API_KEY"

# Check API key format
echo "API Key length: ${#MARKER_API_KEY}"
```

### Debug Logging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export LOG_FORMAT=console

# Start service
python dev_start.py
```

### Verbose Output
```python
# Add to your test script for detailed output
import requests
import json

response = requests.post(
    "http://localhost:8002/v1/convert-json",
    headers={"X-Service-Token": "dev-token", "Content-Type": "application/json"},
    json={"file_content": base64_content, "filename": "test.pdf"}
)

print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
```

## 🧪 Test Files and Data

### Sample Test Files
```bash
# Create test directory
mkdir -p tests/test_files

# Text file
echo "# Test Document\n\nThis is a test." > tests/test_files/test.txt

# You can also use the existing test files:
ls tests/test_files/
```

### Test Data Generation
```python
# Generate base64 content for testing
import base64

def generate_test_base64(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()
    return base64.b64encode(content).decode()

# Usage
base64_content = generate_test_base64('tests/test_files/test.pdf')
print(f"Base64 length: {len(base64_content)}")
```

### Load Testing
```bash
# Simple load test with curl
for i in {1..10}; do
  echo "Request $i"
  curl -X POST http://localhost:8002/v1/convert \
    -H "X-Service-Token: dev-token" \
    -F "file=@tests/test_files/test.txt" \
    -w "Time: %{time_total}s\n" &
done
wait
```

## 🔧 Development Workflow

### Code Changes
```bash
# Service auto-reloads in dev mode
# Just edit files and test

# Force restart if needed
Ctrl+C
python dev_start.py
```

### Testing New Features
```bash
# 1. Make code changes
# 2. Service auto-reloads
# 3. Test with curl or browser
# 4. Check logs for errors
# 5. Repeat
```

### Performance Testing
```python
import time
import requests

def test_performance():
    start = time.time()
    
    response = requests.post(
        "http://localhost:8002/v1/convert",
        headers={"X-Service-Token": "dev-token"},
        files={"file": open("tests/test_files/test.pdf", "rb")}
    )
    
    end = time.time()
    
    print(f"Status: {response.status_code}")
    print(f"Time: {end - start:.2f}s")
    print(f"Processing time: {response.json().get('processing_time', 'N/A')}s")

test_performance()
```

## 📝 Development Scripts

### Auto-test Script
```bash
#!/bin/bash
# save as test_dev.sh

echo "Testing Markdown Service..."

# Health check
echo "1. Health check..."
curl -s http://localhost:8002/health | jq '.status'

# File upload
echo "2. File upload test..."
curl -s -X POST http://localhost:8002/v1/convert \
  -H "X-Service-Token: dev-token" \
  -F "file=@tests/test_files/test.txt" | jq '.success'

# JSON conversion
echo "3. JSON conversion test..."
base64_content=$(base64 tests/test_files/test.txt | tr -d '\n')
curl -s -X POST http://localhost:8002/v1/convert-json \
  -H "Content-Type: application/json" \
  -H "X-Service-Token: dev-token" \
  -d '{"file_content":"'$base64_content'","filename":"test.txt"}' | jq '.success'

echo "Tests completed!"
```

### Monitor Script
```bash
#!/bin/bash
# save as monitor_dev.sh

while true; do
  echo "$(date): Service Status: $(curl -s http://localhost:8002/health | jq -r '.status')"
  sleep 30
done
```

## 🔄 Integration Testing

### With Other Services
```python
# Test integration with json-service
def test_markdown_to_json_flow():
    # Step 1: Convert to markdown
    markdown_response = requests.post(
        "http://localhost:8002/v1/convert-json",
        headers={"X-Service-Token": "dev-token"},
        json={
            "file_content": base64_content,
            "filename": "resume.pdf",
            "output_method": "inline"
        }
    )
    
    markdown_content = markdown_response.json()["markdown_content"]
    
    # Step 2: Convert to JSON (if json-service is running)
    json_response = requests.post(
        "http://localhost:8003/v1/convert",
        headers={"X-Service-Token": "dev-token"},
        json={
            "markdown_content": markdown_content,
            "template": "resume_template"
        }
    )
    
    return json_response.json()
```

### Mock Orchestrator
```python
# Simulate orchestrator behavior
class MockOrchestrator:
    def __init__(self):
        self.base_url = "http://localhost:8002"
        self.token = "dev-token"
    
    def submit_task(self, task):
        response = requests.post(
            f"{self.base_url}/v1/convert-json",
            headers={"X-Service-Token": self.token},
            json=task["payload"]
        )
        return response.json()

# Usage
orchestrator = MockOrchestrator()
result = orchestrator.submit_task({
    "payload": {
        "file_content": base64_content,
        "filename": "test.pdf",
        "request_id": "mock_001"
    }
})
```

## 📊 Monitoring in Development

### Log Analysis
```bash
# Follow logs in real-time
tail -f logs/markdown-service.log

# Search for errors
grep -i error logs/markdown-service.log

# Filter by request ID
grep "req_123" logs/markdown-service.log
```

### System Resources
```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check temp directory
ls -la /tmp/markdown-service/
```

### Performance Metrics
```bash
# Get Prometheus metrics
curl http://localhost:8002/metrics | grep markdown_

# System info
curl -H "X-Service-Token: dev-token" \
  http://localhost:8002/system/info | jq '.file_system'
```

## 🚨 Common Error Scenarios

### Test Error Handling
```bash
# Test invalid file format
echo "not a pdf" > invalid.xyz
curl -X POST http://localhost:8002/v1/convert \
  -H "X-Service-Token: dev-token" \
  -F "file=@invalid.xyz"

# Test missing auth token
curl -X POST http://localhost:8002/v1/convert \
  -F "file=@tests/test_files/test.txt"

# Test invalid base64
curl -X POST http://localhost:8002/v1/convert-json \
  -H "Content-Type: application/json" \
  -H "X-Service-Token: dev-token" \
  -d '{"file_content":"invalid-base64","filename":"test.pdf"}'
```

## 📋 Development Checklist

### Before Development
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] Marker API key configured
- [ ] Service starts without errors
- [ ] Health check passes

### During Development
- [ ] Auto-reload working
- [ ] Logs showing debug information
- [ ] Test endpoints responding
- [ ] Error handling working
- [ ] Performance acceptable

### Before Committing
- [ ] All tests passing
- [ ] No errors in logs
- [ ] API documentation updated
- [ ] Performance regression check
- [ ] Memory leaks check

---

**Development Mode**: markdown-service  
**Version**: 1.0.0  
**Last Updated**: 2024-01-15 