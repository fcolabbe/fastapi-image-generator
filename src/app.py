#!/usr/bin/env python3
"""
FastAPI Image Generator - Punto de entrada para producción
"""

import uvicorn
from generate_image_api import app

if __name__ == "__main__":
    uvicorn.run(
        "generate_image_api:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        access_log=True,
        log_level="info"
    )
