#!/usr/bin/env python3
"""
Script para probar todas las direcciones de pan & scan
"""

import requests
from PIL import Image
import io
from videoeditor import make_pan_scan_video

# Descargar imagen de prueba
print("📥 Descargando imagen de prueba...")
image_url = "https://diarioeldia-s3.cdn.net.ar/s3i233/2025/10/diarioeldia/images/02/31/23/2312395_6bfbb9a763f2750c48d613bd27b191339e04f4dc2c7eeb675fc27762fa4373e3/md.webp"
response = requests.get(image_url, timeout=30)
base_img = Image.open(io.BytesIO(response.content)).convert('RGBA')

headline = "Cambio de mando en Carabineros: General Christian Brebi asume como nuevo Jefe"
highlight = "General Christian Brebi"

# Todas las direcciones disponibles
directions = [
    ("left-to-right", "Panorámica de izquierda a derecha"),
    ("right-to-left", "Panorámica de derecha a izquierda"),
    ("top-to-bottom", "Panorámica de arriba a abajo"),
    ("bottom-to-top", "Panorámica de abajo a arriba"),
    ("zoom-in", "Zoom hacia el centro"),
    ("zoom-out", "Zoom desde el centro"),
    ("diagonal-tl-br", "Diagonal top-left a bottom-right"),
    ("diagonal-tr-bl", "Diagonal top-right a bottom-left"),
]

print(f"\n🎬 Generando {len(directions)} videos de ejemplo...\n")

for direction, description in directions:
    output_path = f"/Users/fcolabbe/Downloads/imagen/video_{direction}.mp4"
    
    print(f"   📹 Generando: {direction}")
    print(f"      {description}")
    
    make_pan_scan_video(
        output_path=output_path,
        image_input=base_img,
        headline=headline,
        highlight=highlight,
        duration=3.0,
        out_w=1080,
        out_h=1920,
        fps=30,
        direction=direction,
        ease_in_out=True
    )
    
    print(f"      ✅ Guardado: {output_path}\n")

print("✨ ¡Todos los videos generados exitosamente!")
print("\n📂 Videos generados:")
for direction, _ in directions:
    print(f"   - video_{direction}.mp4")

print("\n🎥 Para ver todos los videos:")
print("   open /Users/fcolabbe/Downloads/imagen/video_*.mp4")

