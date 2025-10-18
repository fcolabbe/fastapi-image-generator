#!/usr/bin/env python3
"""
Test: Verificar que el video se ajusta automáticamente a la duración del audio
"""

import requests
from PIL import Image
import io
from videoeditor import make_pan_scan_video
import subprocess

# Descargar imagen de prueba
print("📥 Descargando imagen de prueba...")
image_url = "https://diarioeldia-s3.cdn.net.ar/s3i233/2025/10/diarioeldia/images/02/31/23/2312395_6bfbb9a763f2750c48d613bd27b191339e04f4dc2c7eeb675fc27762fa4373e3/md.webp"
response = requests.get(image_url, timeout=30)
base_img = Image.open(io.BytesIO(response.content)).convert('RGBA')

audio_path = "/Users/fcolabbe/Downloads/imagen/argenta.mp3"

# Obtener duración del audio
print("\n🎵 Analizando audio...")
cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
audio_duration = float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
print(f"   Duración del audio: {audio_duration:.2f} segundos")

print("\n🎬 Generando video (duration=5.0, pero debería ajustarse al audio)...")
print("   - Parámetro duration: 5.0 segundos (será ignorado)")
print("   - Audio: argenta.mp3")
print("   - Dirección: right-to-left")

output_path = "/Users/fcolabbe/Downloads/imagen/test_auto_duration.mp4"

make_pan_scan_video(
    output_path=output_path,
    image_input=base_img,
    headline="Cambio de mando en Carabineros: General Christian Brebi asume como nuevo Jefe de la Zona Coquimbo",
    highlight="General Christian Brebi",
    duration=5.0,  # Esto será ignorado porque hay audio
    out_w=1080,
    out_h=1920,
    fps=30,
    direction="right-to-left",
    ease_in_out=True,
    audio_path=audio_path
)

# Verificar duración del video generado
print("\n📊 Verificando duración del video generado...")
cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', output_path]
video_duration = float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
print(f"   Duración del video: {video_duration:.2f} segundos")

# Comparar
difference = abs(video_duration - audio_duration)
print(f"\n📏 Diferencia: {difference:.3f} segundos")

if difference < 0.1:
    print("✅ ¡PERFECTO! El video tiene la misma duración que el audio")
else:
    print(f"⚠️  Hay una diferencia de {difference:.3f}s entre audio y video")

print(f"\n🎥 Video generado: {output_path}")
print(f"   Audio: {audio_duration:.2f}s")
print(f"   Video: {video_duration:.2f}s")
print(f"\n▶️  open {output_path}")

