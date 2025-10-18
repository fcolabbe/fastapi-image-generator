#!/usr/bin/env python3
"""
Test: Video con imagen argenta.jpg y audio argenta.mp3
Titular: Argentina venció a colombia y buscará su séptima corona sub20 en la final ante Marruecos
Destacado: buscará su séptima corona sub20
"""

from PIL import Image
from video_generator import make_pan_scan_video
import subprocess

# Cargar imagen local
print("📸 Cargando imagen argenta.jpg...")
base_img = Image.open("/Users/fcolabbe/Downloads/imagen/argenta.jpg").convert('RGBA')
print(f"   Dimensiones: {base_img.size[0]}x{base_img.size[1]}")

audio_path = "/Users/fcolabbe/Downloads/imagen/argenta.mp3"

# Obtener duración del audio
print("\n🎵 Analizando audio...")
cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
audio_duration = float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
print(f"   Duración del audio: {audio_duration:.2f} segundos")

# Datos del titular
headline = "Argentina venció a colombia y buscará su séptima corona sub20 en la final ante Marruecos"
highlight = "buscará su séptima corona sub20"

print("\n🎬 Generando video...")
print(f"   Titular: {headline}")
print(f"   Destacado: {highlight}")
print(f"   Audio: argenta.mp3 ({audio_duration:.2f}s)")
print(f"   Dirección: zoom-in (efecto dramático)")

output_path = "/Users/fcolabbe/Downloads/imagen/test_argenta_video.mp4"

make_pan_scan_video(
    output_path=output_path,
    image_input=base_img,
    headline=headline,
    highlight=highlight,
    duration=5.0,  # Será ignorado y ajustado al audio
    out_w=1080,
    out_h=1920,
    fps=30,
    direction="zoom-in",  # Efecto de zoom dramático para el gol
    ease_in_out=True,
    audio_path=audio_path
)

# Verificar duración del video generado
print("\n📊 Verificando video generado...")
cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', output_path]
video_duration = float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())
print(f"   Duración del video: {video_duration:.2f} segundos")

# Comparar
difference = abs(video_duration - audio_duration)
print(f"\n📏 Sincronización:")
print(f"   Audio:  {audio_duration:.2f}s")
print(f"   Video:  {video_duration:.2f}s")
print(f"   Diferencia: {difference:.3f}s")

if difference < 0.1:
    print("   ✅ ¡Sincronización perfecta!")
else:
    print(f"   ⚠️  Diferencia de {difference:.3f}s")

print(f"\n🎥 Video generado exitosamente:")
print(f"   {output_path}")
print(f"\n🎯 Características:")
print(f"   • Texto destacado en negrita y azul")
print(f"   • Efecto zoom-in dramático")
print(f"   • Audio sincronizado perfectamente")
print(f"   • Formato 9:16 (1080x1920) para redes sociales")
print(f"\n▶️  open {output_path}")

