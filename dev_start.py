#!/usr/bin/env python3
"""
Development mode startup script for Markdown Service.
"""
import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set development mode
os.environ["DEV_MODE"] = "true"

if __name__ == "__main__":
    # Start server with hot reload
    uvicorn.run(
        "src.markdown_service.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="debug"
    )
