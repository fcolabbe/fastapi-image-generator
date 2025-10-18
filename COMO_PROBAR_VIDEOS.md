# 🎬 Cómo Probar la Creación de Videos

## 📋 Tabla de Contenidos
1. [Prueba Local con Python](#prueba-local-con-python)
2. [Prueba con API usando curl](#prueba-con-api-usando-curl)
3. [Prueba desde n8n](#prueba-desde-n8n)
4. [Parámetros Disponibles](#parámetros-disponibles)
5. [Ejemplos de Respuesta](#ejemplos-de-respuesta)

---

## 1. 🐍 Prueba Local con Python

### Opción A: Script Simple (sin audio)

```bash
cd /Users/fcolabbe/Downloads/imagen
python3 << EOF
from PIL import Image
from video_generator import make_pan_scan_video

base_img = Image.open("argenta.webp").convert('RGBA')

make_pan_scan_video(
    output_path="video_test.mp4",
    image_input=base_img,
    headline="Tu titular aquí",
    highlight="texto destacado",
    duration=5.0,
    direction="zoom-in",
    keep_aspect=True
)
print("✅ Video generado: video_test.mp4")
EOF
```

### Opción B: Con Audio

```bash
python3 << EOF
from PIL import Image
from video_generator import make_pan_scan_video

base_img = Image.open("argenta.webp").convert('RGBA')

make_pan_scan_video(
    output_path="video_con_audio.mp4",
    image_input=base_img,
    headline="Argentina venció a colombia y buscará su séptima corona sub20",
    highlight="buscará su séptima corona sub20",
    duration=5.0,  # Se ajustará al audio automáticamente
    direction="zoom-in",
    keep_aspect=True,
    audio_path="argenta.mp3"
)
print("✅ Video generado: video_con_audio.mp4")
EOF
```

### Opción C: Usar script pre-creado

```bash
python3 test_video_simple.py
```

---

## 2. 🌐 Prueba con API usando curl

### A) Video Básico (sin audio)

```bash
curl -X POST \
  -F "headline=Tu titular completo aquí" \
  -F "highlight=texto a destacar" \
  -F "image_url=https://ejemplo.com/imagen.jpg" \
  -F "duration=5.0" \
  -F "direction=zoom-in" \
  -F "fps=30" \
  -F "keep_aspect=true" \
  https://thumbnail.shortenqr.com/generate-video-from-url
```

### B) Video con Audio

```bash
curl -X POST \
  -F "headline=Tu titular completo aquí" \
  -F "highlight=texto a destacar" \
  -F "image_url=https://ejemplo.com/imagen.jpg" \
  -F "direction=left-to-right" \
  -F "fps=30" \
  -F "keep_aspect=true" \
  -F "audio=@/ruta/a/tu/audio.mp3" \
  https://thumbnail.shortenqr.com/generate-video-from-url
```

### C) Video Vertical 9:16 (Instagram/TikTok)

```bash
curl -X POST \
  -F "headline=Tu titular completo aquí" \
  -F "highlight=texto a destacar" \
  -F "image_url=https://ejemplo.com/imagen.jpg" \
  -F "duration=5.0" \
  -F "direction=zoom-in" \
  -F "fps=30" \
  -F "keep_aspect=false" \
  https://thumbnail.shortenqr.com/generate-video-from-url
```

### D) Ejemplo Completo con Imagen Real

```bash
curl -X POST \
  -F "headline=Argentina venció a colombia y buscará su séptima corona sub20 en la final ante Marruecos" \
  -F "highlight=buscará su séptima corona sub20" \
  -F "image_url=https://diarioeldia-s3.cdn.net.ar/s3i233/2025/10/diarioeldia/images/02/31/23/2312395_6bfbb9a763f2750c48d613bd27b191339e04f4dc2c7eeb675fc27762fa4373e3/md.webp" \
  -F "duration=5.0" \
  -F "direction=zoom-in" \
  -F "fps=30" \
  -F "keep_aspect=true" \
  https://thumbnail.shortenqr.com/generate-video-from-url | python3 -m json.tool
```

---

## 3. 🔗 Prueba desde n8n

### Configuración del Nodo HTTP Request

```json
{
  "method": "POST",
  "url": "https://thumbnail.shortenqr.com/generate-video-from-url",
  "sendBody": true,
  "bodyParameters": {
    "parameters": [
      {
        "name": "headline",
        "value": "={{ $json.headline }}"
      },
      {
        "name": "highlight",
        "value": "={{ $json.highlight }}"
      },
      {
        "name": "image_url",
        "value": "={{ $json.image_url }}"
      },
      {
        "name": "duration",
        "value": "5.0"
      },
      {
        "name": "direction",
        "value": "zoom-in"
      },
      {
        "name": "fps",
        "value": "30"
      },
      {
        "name": "keep_aspect",
        "value": "true"
      }
    ]
  },
  "options": {
    "timeout": 120000
  }
}
```

### Con Audio desde n8n

```javascript
// En el nodo HTTP Request, agregar:
{
  "sendBinaryData": true,
  "binaryPropertyName": "audio",
  "bodyParameters": {
    "parameters": [
      // ... otros parámetros ...
      {
        "name": "audio",
        "value": "={{ $binary.audio }}"
      }
    ]
  }
}
```

---

## 4. ⚙️ Parámetros Disponibles

### Parámetros Obligatorios

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `headline` | string | Titular completo a mostrar |
| `highlight` | string | Parte del titular a destacar (negrita + azul) |
| `image_url` | string | URL de la imagen base |

### Parámetros Opcionales

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `duration` | float | 5.0 | Duración en segundos (ignorado si hay audio) |
| `direction` | string | "left-to-right" | Dirección del efecto pan & scan |
| `fps` | int | 30 | Frames por segundo |
| `keep_aspect` | bool | true | Mantener aspecto original de la imagen |
| `audio` | file | null | Archivo de audio (mp3, wav, etc.) |

### Direcciones Disponibles

- `left-to-right` - Pan de izquierda a derecha
- `right-to-left` - Pan de derecha a izquierda
- `top-to-bottom` - Pan de arriba a abajo
- `bottom-to-top` - Pan de abajo a arriba
- `zoom-in` - Zoom in (acercamiento)
- `zoom-out` - Zoom out (alejamiento)
- `diagonal-tl-br` - Diagonal top-left a bottom-right
- `diagonal-tr-bl` - Diagonal top-right a bottom-left

---

## 5. 📊 Ejemplos de Respuesta

### Respuesta Exitosa (sin audio)

```json
{
  "success": true,
  "video_url": "https://thumbnail.shortenqr.com/public/videos/video_20251018_143022_a1b2c3d4.mp4",
  "headline": "Argentina venció a colombia y buscará su séptima corona sub20",
  "highlight": "buscará su séptima corona sub20",
  "duration": 5.0,
  "direction": "zoom-in",
  "fps": 30,
  "format": "992:528",
  "dimensions": "992x528",
  "keep_aspect": true,
  "has_audio": false,
  "timestamp": "2025-10-18T14:30:22.123456"
}
```

### Respuesta Exitosa (con audio)

```json
{
  "success": true,
  "video_url": "https://thumbnail.shortenqr.com/public/videos/video_20251018_143500_e5f6g7h8.mp4",
  "headline": "Argentina venció a colombia y buscará su séptima corona sub20",
  "highlight": "buscará su séptima corona sub20",
  "duration": 23.11,
  "direction": "zoom-in",
  "fps": 30,
  "format": "992:528",
  "dimensions": "992x528",
  "keep_aspect": true,
  "has_audio": true,
  "timestamp": "2025-10-18T14:35:00.654321"
}
```

### Respuesta de Error

```json
{
  "detail": "Could not download image from URL: HTTPSConnectionPool..."
}
```

---

## 🎯 Tips y Recomendaciones

### ⚡ Performance

- Videos SIN audio se generan en ~10-20 segundos
- Videos CON audio dependen de la duración del audio
- Videos más largos (>30s) pueden tomar más tiempo

### 🎨 Calidad Visual

- Usar imágenes de alta resolución (mínimo 1200px de ancho)
- `keep_aspect=true` mantiene proporciones originales (mejor para horizontal)
- `keep_aspect=false` fuerza 9:16 (mejor para redes sociales verticales)

### 🔊 Audio

- Formatos soportados: MP3, WAV, AAC, OGG
- La duración del video se ajusta automáticamente al audio
- El parámetro `duration` es ignorado si hay audio

### 📱 Formato

- **Horizontal** (keep_aspect=true): Web, YouTube, Facebook
- **Vertical 9:16** (keep_aspect=false): Instagram Stories, TikTok, Reels

### 🎬 Efectos

- `zoom-in`: Ideal para deportes, acción, drama
- `left-to-right` / `right-to-left`: Panorámicas, paisajes
- `top-to-bottom`: Edificios, estructuras verticales

---

## 🚀 Despliegue en Servidor

Para probar en servidor de desarrollo:

```bash
# En el servidor
cd /var/www/fastapi-image-generator
git pull origin main
pm2 restart fastapi-image-generator

# Verificar que esté corriendo
pm2 status
pm2 logs fastapi-image-generator --lines 50
```

---

## 📝 Notas Importantes

1. **Logo El Día**: Se incluye automáticamente en todos los videos
2. **Watermark**: "diarioeldia.cl" aparece en la barra lateral
3. **Colores**:
   - Logo: RGB(56, 92, 169) - Azul claro
   - Texto destacado: RGB(0, 64, 145) - Azul oscuro (negrita)
4. **Timeout**: Configurar timeout de al menos 120 segundos en n8n
5. **Caché**: Los videos no se cachean, cada llamada genera un nuevo video

---

## ✅ Checklist de Prueba

- [ ] Video sin audio (5 segundos)
- [ ] Video con audio (duración automática)
- [ ] Video horizontal (keep_aspect=true)
- [ ] Video vertical 9:16 (keep_aspect=false)
- [ ] Diferentes direcciones (zoom-in, left-to-right, etc.)
- [ ] Verificar logo visible
- [ ] Verificar texto destacado en negrita y azul
- [ ] Verificar sincronización de audio
- [ ] Verificar URL pública accesible
- [ ] Verificar calidad del video

---

**¿Necesitas ayuda?** Revisa los logs:
```bash
pm2 logs fastapi-image-generator
```

