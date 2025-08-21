# 🔗 Markdown Service Integration Guide

> **Quick reference for teams developing Orchestrator and other microservices**

## 📋 Service Overview

| Property | Value |
|----------|-------|
| **Service Name** | `markdown-service` |
| **Port** | `8002` |
| **Base URL** | `http://markdown-service:8002` |
| **Purpose** | Document to Markdown conversion with flexible I/O strategies |
| **Dependencies** | Marker API (external) |

## 🚀 Quick Integration Test

```bash
# Health check
curl http://markdown-service:8002/health

# System information
curl -H "X-Service-Token: dev-token" \
  http://markdown-service:8002/system/info

# Test file upload (direct)
curl -X POST http://markdown-service:8002/v1/convert \
  -H "X-Service-Token: dev-token" \
  -F "file=@test.pdf"

# Test JSON conversion (orchestrator style)
curl -X POST http://markdown-service:8002/v1/convert-json \
  -H "Content-Type: application/json" \
  -H "X-Service-Token: dev-token" \
  -d '{
    "file_content": "'$(base64 test.pdf)'",
    "filename": "test.pdf",
    "request_id": "test-001",
    "output_method": "auto"
  }'
```

## 🔌 Core API Endpoints

### 1. POST /v1/convert-json
**Primary endpoint for orchestrator integration**

```json
// Request (Base64 Content)
{
  "file_content": "JVBERi0xLjQ...",
  "filename": "document.pdf",
  "request_id": "orch_batch_001_item_042",
  "output_method": "auto",
  "max_inline_size": 1048576,
  "priority": 1
}

// Response (Inline)
{
  "success": true,
  "markdown_content": "# Document Title\n\nContent...",
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
  }
}

// Response (Reference)
{
  "success": true,
  "markdown_content": null,
  "markdown_url": "/outputs/doc_abc123.md",
  "content_size": 5242880,
  "processing_time": 45.67,
  "output_method": "reference",
  "request_id": "orch_batch_001_item_042"
}
```

### 2. POST /v1/convert
**File upload endpoint for direct calls**

```bash
curl -X POST http://markdown-service:8002/v1/convert \
  -H "X-Service-Token: dev-token" \
  -F "file=@document.pdf"
```

### 3. GET /outputs/{filename}
**Retrieve reference content**

```bash
curl -H "X-Service-Token: dev-token" \
  http://markdown-service:8002/outputs/doc_abc123.md
```

### 4. GET /health
**Service health check**

```json
{
  "status": "healthy",
  "service": "markdown-service",
  "version": "1.0.0",
  "checks": {
    "service_status": true,
    "temp_directory": true,
    "marker_api_configured": true
  }
}
```

## 🏗️ Orchestrator Integration Patterns

### Task Submission
```python
def submit_markdown_conversion(orchestrator, file_data, request_id):
    """Submit document conversion task to orchestrator"""
    task = {
        "service": "markdown-service",
        "operation": "convert-json",
        "payload": {
            "file_content": base64.b64encode(file_data).decode(),
            "filename": "document.pdf",
            "request_id": request_id,
            "output_method": "auto",
            "max_inline_size": 1024 * 1024,  # 1MB
            "priority": 1  # High priority
        },
        "timeout": 300,
        "retry_attempts": 3
    }
    return orchestrator.submit_task(task)
```

### Response Handling
```python
def handle_markdown_response(response):
    """Handle markdown service response"""
    if not response["success"]:
        raise ProcessingError(f"Conversion failed: {response['error']}")
    
    if response["output_method"] == "inline":
        # Content available directly
        markdown_content = response["markdown_content"]
    else:
        # Need to fetch from reference
        markdown_content = fetch_reference_content(
            response["markdown_url"]
        )
    
    return {
        "content": markdown_content,
        "metadata": response["file_info"],
        "processing_time": response["processing_time"]
    }

def fetch_reference_content(markdown_url):
    """Fetch content from reference URL"""
    response = requests.get(
        f"http://markdown-service:8002{markdown_url}",
        headers={"X-Service-Token": "your-token"}
    )
    return response.json()["content"]
```

### Service Chaining
```python
def markdown_to_json_chain(orchestrator, file_data, request_id):
    """Chain markdown conversion with JSON service"""
    
    # Step 1: Convert to markdown
    markdown_task = {
        "service": "markdown-service",
        "operation": "convert-json",
        "payload": {
            "file_content": base64.b64encode(file_data).decode(),
            "filename": "resume.pdf",
            "request_id": f"{request_id}_md",
            "output_method": "auto"
        }
    }
    
    markdown_result = orchestrator.execute_task(markdown_task)
    
    if not markdown_result["success"]:
        raise ProcessingError("Markdown conversion failed")
    
    # Get markdown content
    if markdown_result["output_method"] == "inline":
        markdown_content = markdown_result["markdown_content"]
    else:
        markdown_content = fetch_reference_content(
            markdown_result["markdown_url"]
        )
    
    # Step 2: Convert to JSON
    json_task = {
        "service": "json-service",
        "operation": "convert",
        "payload": {
            "markdown_content": markdown_content,
            "request_id": f"{request_id}_json",
            "template": "resume_template"
        }
    }
    
    return orchestrator.execute_task(json_task)
```

## 📊 Input/Output Strategies

### Input Methods

#### 1. Base64 Content (Recommended for Orchestrator)
```json
{
  "file_content": "JVBERi0xLjQ...",  // Base64 encoded
  "filename": "document.pdf"
}
```

**Pros**: Direct content transfer, no additional storage needed  
**Cons**: Large payloads for big files  
**Use When**: Files < 10MB, direct orchestrator calls

#### 2. URL Reference
```json
{
  "file_url": "s3://bucket/files/document.pdf",
  "filename": "document.pdf"
}
```

**Pros**: Small payloads, supports any file size  
**Cons**: Requires accessible URL, additional network call  
**Use When**: Large files, files in cloud storage

#### 3. File Upload (multipart/form-data)
```bash
curl -F "file=@document.pdf" ...
```

**Pros**: Simple for direct API calls  
**Cons**: Not suitable for orchestrator integration  
**Use When**: Direct service calls, testing

### Output Methods

#### 1. Inline (auto for files < 1MB)
```json
{
  "markdown_content": "# Document content...",
  "markdown_url": null,
  "output_method": "inline"
}
```

**Pros**: Immediate access, no additional requests  
**Cons**: Large response payloads  
**Use When**: Small files, immediate processing needed

#### 2. Reference (auto for files >= 1MB)
```json
{
  "markdown_content": null,
  "markdown_url": "/outputs/doc_abc123.md",
  "output_method": "reference"
}
```

**Pros**: Small response size, memory efficient  
**Cons**: Requires additional request to fetch content  
**Use When**: Large files, batch processing

#### 3. Auto (Recommended)
```json
{
  "output_method": "auto",
  "max_inline_size": 1048576  // 1MB threshold
}
```

**Pros**: Intelligent decision based on content size  
**Use When**: Default behavior for most scenarios

## 🔄 Batch Processing Patterns

### Parallel Batch Processing
```python
def process_batch_parallel(orchestrator, files, batch_id):
    """Process multiple files in parallel"""
    tasks = []
    
    for i, file_data in enumerate(files):
        task = {
            "service": "markdown-service",
            "operation": "convert-json",
            "payload": {
                "file_content": base64.b64encode(file_data["content"]).decode(),
                "filename": file_data["name"],
                "request_id": f"batch_{batch_id}_item_{i}",
                "output_method": "reference",  # Use references for batch
                "priority": 5  # Lower priority for batch
            }
        }
        tasks.append(task)
    
    # Submit all tasks
    results = orchestrator.submit_batch(tasks)
    
    # Collect results
    markdown_contents = []
    for result in results:
        if result["success"]:
            content = fetch_reference_content(result["markdown_url"])
            markdown_contents.append(content)
        else:
            # Handle failed conversions
            log_error(f"Conversion failed: {result['error']}")
    
    return markdown_contents
```

### Sequential Chain Processing
```python
def process_batch_sequential(orchestrator, files, batch_id):
    """Process files sequentially with rate limiting"""
    results = []
    
    for i, file_data in enumerate(files):
        # Convert to markdown
        markdown_result = submit_markdown_conversion(
            orchestrator, file_data["content"], f"batch_{batch_id}_item_{i}"
        )
        
        if markdown_result["success"]:
            # Get content
            if markdown_result["output_method"] == "inline":
                content = markdown_result["markdown_content"]
            else:
                content = fetch_reference_content(markdown_result["markdown_url"])
            
            # Continue with next service
            json_result = submit_json_conversion(
                orchestrator, content, f"batch_{batch_id}_item_{i}_json"
            )
            
            results.append({
                "file": file_data["name"],
                "markdown": content,
                "json": json_result
            })
        
        # Rate limiting
        time.sleep(1)  # Adjust based on API limits
    
    return results
```

## ⚡ Performance Optimization

### File Size Optimization
```python
def optimize_request_strategy(file_size):
    """Choose optimal request strategy based on file size"""
    if file_size < 1024 * 1024:  # < 1MB
        return {
            "input_method": "base64",
            "output_method": "inline",
            "priority": 1
        }
    elif file_size < 10 * 1024 * 1024:  # < 10MB
        return {
            "input_method": "base64",
            "output_method": "reference", 
            "priority": 3
        }
    else:  # >= 10MB
        return {
            "input_method": "url",
            "output_method": "reference",
            "priority": 5
        }
```

### Concurrent Processing
```python
import asyncio
import aiohttp

async def process_files_concurrent(files, max_concurrent=5):
    """Process files with controlled concurrency"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_single_file(session, file_data):
        async with semaphore:
            task = {
                "file_content": base64.b64encode(file_data["content"]).decode(),
                "filename": file_data["name"],
                "output_method": "auto"
            }
            
            async with session.post(
                "http://markdown-service:8002/v1/convert-json",
                headers={"X-Service-Token": "your-token"},
                json=task
            ) as response:
                return await response.json()
    
    async with aiohttp.ClientSession() as session:
        tasks = [process_single_file(session, file_data) for file_data in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return results
```

## 🚨 Error Handling & Resilience

### Retry Strategy
```python
def convert_with_retry(orchestrator, file_data, request_id, max_retries=3):
    """Convert with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            result = submit_markdown_conversion(
                orchestrator, file_data, f"{request_id}_attempt_{attempt}"
            )
            
            if result["success"]:
                return result
            
            # Check if error is retryable
            if result.get("error_code") in ["MARKER_API_ERROR", "PROCESSING_TIMEOUT"]:
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
                continue
            else:
                # Non-retryable error
                raise ProcessingError(f"Non-retryable error: {result['error']}")
                
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
    
    raise ProcessingError("Max retries exceeded")
```

### Circuit Breaker Pattern
```python
class MarkdownServiceCircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call_service(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = "HALF_OPEN"
            else:
                raise ServiceUnavailableError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise
```

## 📊 Monitoring Integration

### Health Check Monitoring
```python
def check_service_health():
    """Check markdown service health"""
    try:
        response = requests.get(
            "http://markdown-service:8002/health",
            timeout=10
        )
        health_data = response.json()
        
        if health_data["status"] != "healthy":
            alert_manager.send_alert(
                "markdown_service_unhealthy",
                f"Service status: {health_data['status']}"
            )
        
        return health_data
        
    except Exception as e:
        alert_manager.send_alert(
            "markdown_service_unreachable",
            f"Health check failed: {str(e)}"
        )
        return None
```

### Performance Metrics
```python
def track_performance_metrics(request_data, response_data):
    """Track key performance metrics"""
    metrics = {
        "processing_time": response_data.get("processing_time", 0),
        "file_size": request_data.get("file_size", 0),
        "output_method": response_data.get("output_method"),
        "success": response_data.get("success", False)
    }
    
    # Send to monitoring system
    prometheus_client.histogram("markdown_processing_time").observe(
        metrics["processing_time"]
    )
    
    prometheus_client.counter("markdown_requests_total").labels(
        output_method=metrics["output_method"],
        success=metrics["success"]
    ).inc()
```

## 🔧 Configuration Management

### Environment Configuration
```python
# Orchestrator configuration for markdown service
MARKDOWN_SERVICE_CONFIG = {
    "url": "http://markdown-service:8002",
    "timeout": 300,
    "retry_attempts": 3,
    "retry_delay": 1.0,
    "max_concurrent": 5,
    "circuit_breaker": {
        "failure_threshold": 5,
        "reset_timeout": 60
    },
    "endpoints": {
        "convert": "/v1/convert-json",
        "health": "/health",
        "outputs": "/outputs/{filename}",
        "metrics": "/metrics"
    }
}
```

### Service Discovery
```python
def discover_markdown_service():
    """Discover markdown service instances"""
    # Using Consul, Eureka, or K8s service discovery
    instances = service_discovery.get_healthy_instances("markdown-service")
    
    return {
        "instances": instances,
        "load_balancer": "round_robin",
        "health_check_interval": 30
    }
```

## 📋 Testing Integration

### Integration Test Example
```python
def test_markdown_integration():
    """Test markdown service integration"""
    # Prepare test data
    test_file = load_test_pdf()
    request_data = {
        "file_content": base64.b64encode(test_file).decode(),
        "filename": "test.pdf",
        "request_id": "test_001",
        "output_method": "auto"
    }
    
    # Call service
    response = requests.post(
        "http://markdown-service:8002/v1/convert-json",
        headers={"X-Service-Token": "dev-token"},
        json=request_data
    )
    
    # Verify response
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "markdown_content" in result or "markdown_url" in result
    assert result["processing_time"] > 0
```

---

**Service**: markdown-service  
**Version**: 1.0.0  
**Last Updated**: 2024-01-15 