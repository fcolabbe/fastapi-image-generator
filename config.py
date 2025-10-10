"""
Configuración de la aplicación FastAPI Image Generator
"""

import os

# URL base del servidor - CAMBIAR POR TU DOMINIO REAL
BASE_URL = os.getenv("BASE_URL", "http://tu-servidor.com")

# Directorio donde se guardan las imágenes públicas
PUBLIC_IMAGES_DIR = "/var/www/fastapi-image-generator/public/images"

# Configuración de logs
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

# Configuración de la aplicación
APP_NAME = "FastAPI Image Generator"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Generate news-style images with headline overlays"
