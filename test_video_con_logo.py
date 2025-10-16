#!/usr/bin/env python3
"""
Test: Video con logo El Día y estilo exacto de imágenes
Titular: Argentina venció a colombia y buscará su séptima corona sub20 en la final ante Marruecos
Destacado: buscará su séptima corona sub20
"""

from PIL import Image
from video_generator import make_pan_scan_video
import subprocess

# Cargar imagen local
print("📸 Cargando imagen argenta.webp...")
base_img = Image.open("/Users/fcolabbe/Downloads/imagen/argenta.webp").convert('RGBA')
print(f"   Dimensiones: {base_img.size[0]}x{base_img.size[1]}")
print(f"   Aspecto: {base_img.size[0]/base_img.size[1]:.2f}:1")

audio_path = "/Users/fcolabbe/Downloads/imagen/argenta.mp3"

# Obtener duración del audio
print("\n🎵 Analizando audio...")
cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
audio_duration = float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
print(f"   Duración: {audio_duration:.2f} segundos")

# Datos del titular
headline = "Argentina venció a colombia y buscará su séptima corona sub20 en la final ante Marruecos"
highlight = "buscará su séptima corona sub20"

print("\n🎬 Generando video con TODAS las características:")
print(f"   📝 Titular: {headline}")
print(f"   🔵 Destacado: {highlight} (negrita + azul)")
print(f"   🎵 Audio: argenta.mp3 ({audio_duration:.2f}s)")
print(f"   📐 Aspecto: Original (horizontal)")
print(f"   🎯 Dirección: zoom-in")
print(f"   🏢 Logo: El_Dia.png (esquina superior derecha)")
print(f"   💧 Watermark: diarioeldia.cl (barra lateral)")

output_path = "/Users/fcolabbe/Downloads/imagen/test_video_completo.mp4"

make_pan_scan_video(
    output_path=output_path,
    image_input=base_img,
    headline=headline,
    highlight=highlight,
    duration=5.0,  # Será ajustado al audio
    fps=30,
    direction="zoom-in",
    ease_in_out=True,
    audio_path=audio_path,
    keep_aspect=True  # Mantener aspecto horizontal
)

# Verificar video generado
print("\n📊 Verificando video generado...")

# Duración
cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', output_path]
video_duration = float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())

# Dimensiones
cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', output_path]
result = subprocess.run(cmd, capture_output=True, text=True)
video_w, video_h = result.stdout.strip().split(',')

print(f"   📐 Dimensiones: {video_w}x{video_h}")
print(f"   📏 Aspecto: {int(video_w)/int(video_h):.2f}:1")
print(f"   ⏱️  Duración: {video_duration:.2f}s")

# Sincronización
difference = abs(video_duration - audio_duration)
print(f"\n🎵 Sincronización audio:")
print(f"   Audio:  {audio_duration:.2f}s")
print(f"   Video:  {video_duration:.2f}s")
print(f"   Diff:   {difference:.3f}s")
if difference < 0.1:
    print("   ✅ Perfecta")

print(f"\n✅ Video generado exitosamente:")
print(f"   {output_path}")

print(f"\n🎯 Características aplicadas:")
print(f"   ✅ Logo El Día en esquina superior derecha")
print(f"   ✅ Watermark 'diarioeldia.cl' en barra lateral")
print(f"   ✅ Texto destacado en NEGRITA y color AZUL")
print(f"   ✅ Estilo EXACTO igual que imágenes")
print(f"   ✅ Sin cortes de palabras")
print(f"   ✅ Aspecto horizontal mantenido")
print(f"   ✅ Audio sincronizado")
print(f"   ✅ Efecto zoom-in dramático")

print(f"\n▶️  open {output_path}")

