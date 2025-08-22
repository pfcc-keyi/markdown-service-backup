#!/usr/bin/env python3
"""
Production startup script for Markdown Service.
"""
import os
import sys
import uvicorn

def main():
    """Start Markdown Service in production mode."""
    
    print("🚀 Starting Markdown Service in Production Mode")
    print("=" * 50)
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    workers = int(os.getenv("WORKERS", "1"))
    
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"📝 Log Level: {log_level}")
    print(f"👥 Workers: {workers}")
    print()
    
    # Check required environment variables
    marker_api_key = os.getenv("MARKER_API_KEY")
    if not marker_api_key:
        print("❌ ERROR: MARKER_API_KEY environment variable is required!")
        sys.exit(1)
    else:
        print(f"✅ Marker API Key: {marker_api_key[:8]}...")
    
    service_token = os.getenv("SERVICE_TOKEN")
    if not service_token:
        print("❌ ERROR: SERVICE_TOKEN environment variable is required!")
        sys.exit(1)
    else:
        print(f"✅ Service Token: {service_token[:8]}...")
    
    print()
    print("🚀 Starting Markdown Service...")
    print("   Press Ctrl+C to stop")
    print()
    
    try:
        uvicorn.run(
            "src.markdown_service.main:app",
            host=host,
            port=port,
            reload=False,  # No reload in production
            log_level=log_level,
            workers=workers
        )
    except KeyboardInterrupt:
        print("\n🛑 Markdown Service stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start Markdown Service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 