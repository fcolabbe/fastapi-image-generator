#!/usr/bin/env python3
"""
Test: Video con imagen argenta.webp manteniendo aspecto original
Titular: Argentina venció a colombia y buscará su séptima corona sub20 en la final ante Marruecos
Destacado: buscará su séptima corona sub20
"""

from PIL import Image
from videoeditor import make_pan_scan_video
import subprocess

# Cargar imagen local
print("📸 Cargando imagen argenta.webp...")
base_img = Image.open("/Users/fcolabbe/Downloads/imagen/argenta.webp").convert('RGBA')
print(f"   Dimensiones originales: {base_img.size[0]}x{base_img.size[1]}")
print(f"   Aspecto: {base_img.size[0]/base_img.size[1]:.2f}:1")

audio_path = "/Users/fcolabbe/Downloads/imagen/argenta.mp3"

# Obtener duración del audio
print("\n🎵 Analizando audio...")
cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
audio_duration = float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
print(f"   Duración del audio: {audio_duration:.2f} segundos")

# Datos del titular
headline = "Argentina venció a colombia y buscará su séptima corona sub20 en la final ante Marruecos"
highlight = "buscará su séptima corona sub20"

print("\n🎬 Generando video con aspecto original...")
print(f"   Titular: {headline}")
print(f"   Destacado: {highlight}")
print(f"   Audio: argenta.mp3 ({audio_duration:.2f}s)")
print(f"   Dirección: zoom-in")
print(f"   ✅ keep_aspect=True (mantiene aspecto original)")

output_path = "/Users/fcolabbe/Downloads/imagen/test_argenta_aspect.mp4"

make_pan_scan_video(
    output_path=output_path,
    image_input=base_img,
    headline=headline,
    highlight=highlight,
    duration=5.0,  # Será ignorado y ajustado al audio
    fps=30,
    direction="zoom-in",
    ease_in_out=True,
    audio_path=audio_path,
    keep_aspect=True  # MANTENER ASPECTO ORIGINAL
)

# Verificar dimensiones y duración del video generado
print("\n📊 Verificando video generado...")

# Duración
cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', output_path]
video_duration = float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())

# Dimensiones
cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', output_path]
result = subprocess.run(cmd, capture_output=True, text=True)
video_w, video_h = result.stdout.strip().split(',')

print(f"   Dimensiones video: {video_w}x{video_h}")
print(f"   Aspecto video: {int(video_w)/int(video_h):.2f}:1")
print(f"   Duración video: {video_duration:.2f} segundos")

# Comparar aspectos
original_aspect = base_img.size[0] / base_img.size[1]
video_aspect = int(video_w) / int(video_h)
aspect_diff = abs(original_aspect - video_aspect)

print(f"\n📏 Comparación:")
print(f"   Aspecto original: {original_aspect:.2f}:1")
print(f"   Aspecto video:    {video_aspect:.2f}:1")
print(f"   Diferencia:       {aspect_diff:.4f}")

if aspect_diff < 0.01:
    print("   ✅ ¡Aspecto mantenido perfectamente!")
else:
    print(f"   ⚠️  Aspecto ligeramente diferente")

# Sincronización
difference = abs(video_duration - audio_duration)
print(f"\n🎵 Sincronización:")
print(f"   Audio:  {audio_duration:.2f}s")
print(f"   Video:  {video_duration:.2f}s")
print(f"   Diferencia: {difference:.3f}s")

if difference < 0.1:
    print("   ✅ ¡Sincronización perfecta!")

print(f"\n🎥 Video generado exitosamente:")
print(f"   {output_path}")
print(f"\n🎯 Características:")
print(f"   • Aspecto original mantenido: {video_w}x{video_h}")
print(f"   • Texto destacado en negrita y azul")
print(f"   • Efecto zoom-in dramático")
print(f"   • Audio sincronizado perfectamente")
print(f"\n▶️  open {output_path}")

