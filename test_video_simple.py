#!/usr/bin/env python3
"""
Test simple: Crear video con imagen local
"""

from PIL import Image
from video_generator import make_pan_scan_video

print("🎬 Generando video de prueba...\n")

# Cargar imagen
base_img = Image.open("argenta.webp").convert('RGBA')

# Generar video
make_pan_scan_video(
    output_path="video_prueba.mp4",
    image_input=base_img,
    headline="Argentina venció a colombia y buscará su séptima corona sub20 en la final ante Marruecos",
    highlight="buscará su séptima corona sub20",
    duration=5.0,
    fps=30,
    direction="zoom-in",
    keep_aspect=True,
    audio_path="argenta.mp3"  # Opcional: quita esta línea si quieres video sin audio
)

print("\n✅ Video generado: video_prueba.mp4")
print("▶️  open video_prueba.mp4")
