#!/usr/bin/env python3
"""
Test: Verificar colores exactos que se están usando
"""

from PIL import Image

# Cargar el logo
print("🔍 Analizando Logo El_Dia.png...")
logo = Image.open("/Users/fcolabbe/Downloads/imagen/El_Dia.png")
print(f"   Modo: {logo.mode}")
print(f"   Tamaño: {logo.size}")

# Muestrear algunos píxeles del logo (centro y esquinas)
samples = [
    (300, 300),  # Centro
    (100, 100),  # Esquina superior izquierda
    (500, 100),  # Esquina superior derecha
    (300, 450),  # Parte inferior
]

print(f"\n📊 Muestras de colores del logo:")
for x, y in samples:
    pixel = logo.getpixel((x, y))
    print(f"   Posición ({x},{y}): RGB{pixel}")

# Definir el color del texto destacado
highlight_color = (0, 64, 145)
print(f"\n🔵 Color del texto destacado esperado:")
print(f"   RGB{highlight_color}")
print(f"   En decimal: R={highlight_color[0]}, G={highlight_color[1]}, B={highlight_color[2]}")
print(f"   En hexadecimal: #{highlight_color[0]:02X}{highlight_color[1]:02X}{highlight_color[2]:02X}")

# Crear una imagen de muestra con el color exacto
muestra = Image.new('RGB', (200, 100), highlight_color)
muestra.save("/Users/fcolabbe/Downloads/imagen/color_azul_referencia.png")
print(f"\n✅ Imagen de referencia del color azul guardada:")
print(f"   /Users/fcolabbe/Downloads/imagen/color_azul_referencia.png")

print(f"\n💡 IMPORTANTE:")
print(f"   - El texto destacado usa RGB(0, 64, 145) - azul OSCURO")
print(f"   - Este NO es el mismo azul del logo El Día")
print(f"   - El logo tiene sus propios colores (azul más claro)")
print(f"   - Ambos colores deben verse DIFERENTES en el video")

