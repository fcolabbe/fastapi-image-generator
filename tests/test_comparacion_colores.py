#!/usr/bin/env python3
"""
Test: Comparar colores del logo y texto destacado entre imagen y video
"""

from PIL import Image, ImageDraw, ImageFont
import sys
sys.path.insert(0, '/Users/fcolabbe/Downloads/imagen')

# Importar la función de creación de imagen
from generate_image_api import _create_composite_image

# Cargar imagen base
print("📸 Generando imagen de referencia...")
base_img = Image.open("/Users/fcolabbe/Downloads/imagen/argenta.webp").convert('RGBA')

headline = "Argentina venció a colombia y buscará su séptima corona sub20 en la final ante Marruecos"
highlight = "buscará su séptima corona sub20"

# Generar imagen de referencia
result_img = _create_composite_image(
    base_img,
    headline=headline,
    highlight=highlight,
    instagram_format=False
)

# Guardar
output_path = "/Users/fcolabbe/Downloads/imagen/test_imagen_referencia.png"
result_img.save(output_path)
print(f"✅ Imagen guardada: {output_path}")

# Analizar colores en diferentes puntos
print("\n🔍 Analizando colores:")

# Analizar el logo (esquina superior derecha)
logo_x = result_img.size[0] - 50
logo_y = 50
logo_pixel = result_img.getpixel((logo_x, logo_y))
print(f"\n📸 Logo (posición {logo_x},{logo_y}):")
print(f"   RGBA: {logo_pixel}")

# Buscar texto azul en la parte inferior (donde está el titular)
# El texto debería estar en la parte inferior
text_y = int(result_img.size[1] * 0.85)  # 85% de la altura
found_blue = False

for x in range(100, result_img.size[0] - 100, 10):
    try:
        pixel = result_img.getpixel((x, text_y))
        # Buscar el azul específico (0, 64, 145)
        if pixel[0] <= 10 and 60 <= pixel[1] <= 70 and 140 <= pixel[2] <= 150:
            print(f"\n🔵 Texto destacado encontrado en ({x},{text_y}):")
            print(f"   RGBA: {pixel}")
            print(f"   RGB: ({pixel[0]}, {pixel[1]}, {pixel[2]})")
            if pixel[0:3] == (0, 64, 145):
                print(f"   ✅ Color EXACTO: (0, 64, 145)")
            else:
                print(f"   ⚠️  Color aproximado a (0, 64, 145)")
            found_blue = True
            break
    except:
        continue

if not found_blue:
    print(f"\n⚠️  No se encontró texto azul en la búsqueda automática")
    print(f"   Verifica manualmente la imagen: {output_path}")

print(f"\n📊 Colores esperados:")
print(f"   Texto destacado: RGB(0, 64, 145) - Azul oscuro")
print(f"   Logo: Colores originales del PNG")

print(f"\n▶️  open {output_path}")

