#!/usr/bin/env python3
"""
Test script para probar la generación de video con audio
"""

import requests
from PIL import Image
import io
from video_generator import make_pan_scan_video

# Descargar imagen de prueba
print("📥 Descargando imagen de prueba...")
image_url = "https://diarioeldia-s3.cdn.net.ar/s3i233/2025/10/diarioeldia/images/02/31/23/2312395_6bfbb9a763f2750c48d613bd27b191339e04f4dc2c7eeb675fc27762fa4373e3/md.webp"
response = requests.get(image_url, timeout=30)
base_img = Image.open(io.BytesIO(response.content)).convert('RGBA')

print("🎬 Generando video con efecto pan & scan + AUDIO...")
print("   - Titular: Cambio de mando en Carabineros")
print("   - Highlight: General Christian Brebi")
print("   - Duración: 5 segundos")
print("   - Dirección: left-to-right")
print("   - FPS: 30")
print("   - Audio: argenta.mp3 🎵")

# Generar video
output_path = "/Users/fcolabbe/Downloads/imagen/test_video_with_audio.mp4"
audio_path = "/Users/fcolabbe/Downloads/imagen/argenta.mp3"

make_pan_scan_video(
    output_path=output_path,
    image_input=base_img,
    headline="Cambio de mando en Carabineros: General Christian Brebi asume como nuevo Jefe de la Zona Coquimbo",
    highlight="General Christian Brebi",
    duration=5.0,
    out_w=1080,
    out_h=1920,
    fps=30,
    direction="left-to-right",
    ease_in_out=True,
    audio_path=audio_path
)

print(f"\n✅ Video con audio generado exitosamente: {output_path}")
print(f"📹 Formato: 1080x1920 (9:16)")
print(f"⏱️  Duración: 5 segundos")
print(f"🎵 Audio: incluido")
print(f"\n🎥 Puedes reproducirlo con: open {output_path}")

