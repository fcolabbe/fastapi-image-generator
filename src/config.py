"""
Configuración de la aplicación FastAPI Image Generator
"""

import os
from pathlib import Path
from dotenv import load_dotenv

defaultOptions = """BASE_URL = "https://tu-sitio.com"
PUBLIC_IMAGES_DIR = "/var/www/fastapi-image-generator/public/images"
PUBLIC_VIDEOS_DIR = "/var/www/fastapi-image-generator/public/videos"

DEFAULT_LOG_LEVEL = "info"
"""


class Config:
    def __init__(self):
        path_root = Path(__file__).resolve().parent.parent
        if not os.path.exists(f"{path_root}/.env"):
            envfile = open(f"{path_root}/.env", "w")
            envfile.write(defaultOptions)
            envfile.close()

        load_dotenv()

        # Configuración de la aplicación
        self.ROOT_PATH = path_root
        self.APP_NAME = "FastAPI Image Generator"
        self.APP_VERSION = "1.1.0"
        self.APP_DESCRIPTION = "Generate news-style images with headline overlays"

        # URL base del servidor - CAMBIAR POR TU DOMINIO REAL
        self.BASE_URL = os.getenv("BASE_URL", "https://thumbnail.shortenqr.com")

        # Directorio donde se guardan las imágenes públicas
        self.PUBLIC_IMAGES_DIR = os.getenv("PUBLIC_IMAGES_DIR")
        self.PUBLIC_VIDEOS_DIR = os.getenv("PUBLIC_VIDEOS_DIR")

        # Crear directorio de imágenes públicas si no existe
        os.makedirs(self.PUBLIC_IMAGES_DIR, exist_ok=True)
        os.makedirs(self.PUBLIC_VIDEOS_DIR, exist_ok=True)

        # Configuración de logs
        self.LOG_LEVEL = os.getenv("DEFAULT_LOG_LEVEL", "info")
