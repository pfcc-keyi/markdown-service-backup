# Markdown Service - Orchestrator Integration Guide

## 概述

Markdown Service 设计了灵活的文件输入输出策略，专门为与 orchestrator 编排服务集成而优化。

## 输入策略

### 1. 文件上传模式 (适合直接调用)
```bash
POST /v1/convert
Content-Type: multipart/form-data

curl -X POST "http://localhost:8002/v1/convert" \
  -H "X-Service-Token: dev-token" \
  -F "file=@document.pdf"
```

### 2. JSON模式 (适合orchestrator调用)
```bash
POST /v1/convert-json
Content-Type: application/json

# Base64 内容模式
{
  "file_content": "JVBERi0xLjQ...",  // base64 encoded
  "filename": "document.pdf",
  "request_id": "orch_12345",
  "output_method": "auto",
  "max_inline_size": 1048576,
  "priority": 1
}

# URL 引用模式
{
  "file_url": "s3://bucket/files/document.pdf",
  "filename": "document.pdf",
  "request_id": "orch_12345",
  "output_method": "reference"
}
```

## 输出策略

### 1. 内联返回 (inline)
适合小文档，直接在响应中返回内容：
```json
{
  "success": true,
  "markdown_content": "# Document Title\n\nContent...",
  "markdown_url": null,
  "content_size": 1024,
  "output_method": "inline"
}
```

### 2. 引用返回 (reference)
适合大文档，返回文件引用：
```json
{
  "success": true,
  "markdown_content": null,
  "markdown_url": "/outputs/doc_abc123.md",
  "content_size": 5242880,
  "output_method": "reference"
}
```

### 3. 自动选择 (auto)
根据内容大小自动选择：
- < 1MB: 内联返回
- >= 1MB: 引用返回

## Orchestrator 集成示例

### 1. 任务提交
```python
# Orchestrator 提交任务
task = {
    "service": "markdown-service",
    "operation": "convert-json",
    "payload": {
        "file_content": base64_content,
        "filename": "resume.pdf",
        "request_id": "batch_001_item_042",
        "output_method": "auto",
        "priority": 1,
        "callback_url": "http://orchestrator:8000/callbacks/markdown"
    },
    "timeout": 300
}
```

### 2. 结果处理
```python
# Orchestrator 处理响应
if response["success"]:
    if response["output_method"] == "inline":
        # 直接使用 markdown_content
        markdown = response["markdown_content"]
    else:
        # 通过引用获取内容
        content_response = requests.get(
            f"http://markdown-service:8002{response['markdown_url']}",
            headers={"X-Service-Token": token}
        )
        markdown = content_response.json()["content"]
    
    # 传递给下一个服务 (json-service)
    next_task = {
        "service": "json-service",
        "operation": "convert",
        "payload": {
            "markdown_content": markdown,
            "request_id": response["request_id"]
        }
    }
```

## 优势分析

### 1. 灵活性
- **多种输入方式**：支持直接上传、base64、URL引用
- **智能输出**：根据内容大小自动选择返回方式
- **统一接口**：orchestrator 只需调用一个接口

### 2. 性能优化
- **内存友好**：大文件不占用响应内存
- **网络优化**：避免传输大量数据
- **存储管理**：自动清理临时文件

### 3. 可扩展性
- **异步支持**：支持callback机制
- **优先级控制**：支持任务优先级
- **监控集成**：提供详细的处理指标

## 文件生命周期

```
1. 输入处理
   ├── Base64解码 或 URL下载
   ├── 存储到临时目录
   └── 生成文件元数据

2. 转换处理
   ├── 调用 Marker API
   ├── 获取 markdown 内容
   └── 记录处理时间

3. 输出处理
   ├── 判断输出方式
   ├── 内联：直接返回
   └── 引用：存储文件 + 返回URL

4. 清理
   ├── 删除临时输入文件
   └── 定期清理过期输出文件
```

## 配置建议

### 环境变量
```bash
# 核心配置
MARKER_API_KEY=your-api-key
DEV_MODE=false

# 文件处理
MAX_FILE_SIZE=52428800    # 50MB
TEMP_DIR=/tmp/markdown-service
REQUEST_TIMEOUT=300       # 5分钟

# 输出控制
MAX_INLINE_SIZE=1048576   # 1MB

# 清理策略
CLEANUP_INTERVAL=3600     # 1小时
MAX_FILE_AGE=86400       # 24小时
```

### Orchestrator 配置
```yaml
services:
  markdown-service:
    url: "http://markdown-service:8002"
    timeout: 300
    retry_attempts: 3
    endpoints:
      convert: "/v1/convert-json"
      health: "/health"
      outputs: "/outputs/{filename}"
```

## 监控和诊断

### 健康检查
```bash
GET /health
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

### 系统信息
```bash
GET /system/info
{
  "service": "markdown-service",
  "version": "1.0.0",
  "file_system": {
    "temp_file_count": 5,
    "output_file_count": 12,
    "total_size_mb": 45.2,
    "free_space_mb": 1024.0,
    "usage_percent": 15.3
  }
}
```

## 错误处理

所有错误都返回一致的响应格式：
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

这种设计确保了 markdown-service 能够高效地与 orchestrator 集成，同时保持良好的性能和可维护性。 