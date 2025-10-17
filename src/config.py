"""
Configuración de la aplicación FastAPI Image Generator
"""

import os
from dotenv import load_dotenv

defaultOptions = """BASE_URL = "https://tu-sitio.com"
PUBLIC_IMAGES_DIR = "/var/www/fastapi-image-generator/public/images"

DEFAULT_LOG_LEVEL = "info"
"""


class Config:
    def __init__(self):
        if not os.path.exists("../.env"):
            envfile = open("../.env", "w")
            envfile.write(defaultOptions)
            envfile.close()

        load_dotenv()

        # Configuración de la aplicación
        self.APP_NAME = "FastAPI Image Generator"
        self.APP_VERSION = "1.0.0"
        self.APP_DESCRIPTION = "Generate news-style images with headline overlays"

        # URL base del servidor - CAMBIAR POR TU DOMINIO REAL
        self.BASE_URL = os.getenv("BASE_URL", "https://thumbnail.shortenqr.com")

        # Directorio donde se guardan las imágenes públicas
        self.PUBLIC_IMAGES_DIR = "./fastapi-image-generator/public/images"

        # Crear directorio de imágenes públicas si no existe
        os.makedirs(self.PUBLIC_IMAGES_DIR, exist_ok=True)

        # Configuración de logs
        self.LOG_LEVEL = os.getenv("DEFAULT_LOG_LEVEL", "info")
