"""Script de prueba para diagnosticar problemas con la API."""

import requests

# Probar la API
url = "http://localhost:8000/generate-image"

files = {
    'image': ('nota.webp', open('/Users/fcolabbe/Downloads/imagen/nota.webp', 'rb'), 'image/webp')
}

data = {
    'headline': 'El turismo Wellness Summit transforma la región: expertos internacionales destacan potencial',
    'highlight': 'El turismo Wellness Summit transforma la región:'
}

print("Enviando solicitud a la API...")
try:
    response = requests.post(url, files=files, data=data)
    print(f"Status code: {response.status_code}")
    print(f"Headers: {response.headers}")
    print(f"Response length: {len(response.content)} bytes")
    
    if response.status_code == 200:
        with open('resultado_test.png', 'wb') as f:
            f.write(response.content)
        print("✓ Imagen generada exitosamente: resultado_test.png")
    else:
        print(f"✗ Error: {response.text}")
        
except Exception as e:
    print(f"✗ Exception: {e}")

