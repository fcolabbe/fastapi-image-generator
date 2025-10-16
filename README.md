# FastAPI Image Generator - Generador de Imágenes de Noticias

Una aplicación FastAPI que genera imágenes compuestas estilo noticia con texto destacado integrado.

## Características

- **API REST** para generar imágenes compuestas
- **Soporte para imágenes locales y URLs**
- **Texto destacado integrado** con color personalizado y formato bold
- **Wrapping inteligente** que nunca corta palabras
- **Líneas de ancho variable** y centradas automáticamente
- **Compatibilidad multiplataforma** (macOS/Linux/Windows)
- **Alineación vertical perfecta** entre texto regular y bold

## Instalación

```bash
# Clonar el repositorio
git clone <repository-url>
cd imagen

# Instalar dependencias
pip install fastapi uvicorn pillow requests

# Ejecutar la aplicación
python3 generate_image_api.py
```

## Uso

La aplicación estará disponible en `http://localhost:8000`

### Endpoints

#### 1. Generar imagen desde archivo local
```bash
curl -X POST \
  -F "headline=Título de la noticia" \
  -F "highlight=texto destacado" \
  -F "image=@imagen.jpg" \
  http://localhost:8000/generate-image
```

**Respuesta:**
```json
{
  "success": true,
  "image_url": "http://tu-servidor.com/public/images/generated_20250101_123456_abc12345.png",
  "headline": "Título de la noticia",
  "highlight": "texto destacado",
  "timestamp": "2025-01-01T12:34:56.789Z"
}
```

#### 2. Generar imagen desde URL
```bash
curl -X POST \
  -F "headline=Título de la noticia" \
  -F "highlight=texto destacado" \
  -F "image_url=https://ejemplo.com/imagen.jpg" \
  http://localhost:8000/generate-image-from-url
```

**Respuesta:**
La API ahora genera automáticamente **AMBAS versiones** (horizontal para web/Facebook e Instagram vertical 4:5):

```json
{
  "success": true,
  "images": {
    "horizontal": {
      "url": "https://tu-servidor.com/public/images/generated_20250101_123456_abc12345.png",
      "format": "original",
      "description": "Imagen horizontal para web/Facebook"
    },
    "instagram": {
      "url": "https://tu-servidor.com/public/images/generated_20250101_123457_def67890.png",
      "format": "4:5",
      "dimensions": "1080x1350",
      "description": "Imagen vertical optimizada para Instagram"
    }
  },
  "headline": "Título de la noticia",
  "highlight": "texto destacado",
  "timestamp": "2025-01-01T12:34:56.789Z"
}
```

## Parámetros

- **headline**: El titular completo de la noticia
- **highlight**: El texto que se destacará (debe estar contenido en el headline)
- **image**: Archivo de imagen local (para endpoint `/generate-image`)
- **image_url**: URL de la imagen (para endpoint `/generate-image-from-url`)
- **recorte** *(opcional)*: ROI para recorte Instagram como "x,y,w,h" en valores 0..1
  - Ejemplo: `"0.14,0,0.72,1"` (recorta 14% izquierda, mantiene 72% ancho, altura completa)
  - Si no se especifica, usa recorte centrado automático

## Formatos Generados

Cada llamada a la API genera automáticamente **2 imágenes**:

### 1. **Versión Horizontal** (Original)
- Mantiene las dimensiones originales de la imagen
- Optimizado para web y Facebook
- Formato panorámico

### 2. **Versión Instagram** (4:5)
- Dimensiones: 1080x1350px (ratio 4:5)
- Recorte inteligente y centrado
- Optimizado para Instagram y redes verticales

## Ejemplos de Uso

### Ejemplo 1: Noticia de Carabineros (genera ambas versiones)
```bash
curl -X POST \
  -F "headline=Cambio de mando en Carabineros: General Christian Brebi asume como nuevo Jefe de la Zona Coquimbo" \
  -F "highlight=General Christian Brebi" \
  -F "image_url=https://diarioeldia-s3.cdn.net.ar/s3i233/2025/10/diarioeldia/images/02/31/23/2312395_6bfbb9a763f2750c48d613bd27b191339e04f4dc2c7eeb675fc27762fa4373e3/md.webp" \
  http://localhost:8000/generate-image-from-url
```

**Respuesta:**
```json
{
  "success": true,
  "images": {
    "horizontal": {
      "url": "https://thumbnail.shortenqr.com/public/images/generated_20250110_150000_abc123.png",
      "format": "original",
      "description": "Imagen horizontal para web/Facebook"
    },
    "instagram": {
      "url": "https://thumbnail.shortenqr.com/public/images/generated_20250110_150001_def456.png",
      "format": "4:5",
      "dimensions": "1080x1350",
      "description": "Imagen vertical optimizada para Instagram"
    }
  },
  "headline": "Cambio de mando en Carabineros: General Christian Brebi asume como nuevo Jefe de la Zona Coquimbo",
  "highlight": "General Christian Brebi",
  "timestamp": "2025-01-10T15:00:01.123Z"
}
```

### Ejemplo 2: Noticia de Combarbalá
```bash
curl -X POST \
  -F "headline=Terror en Combarbalá: Sujeto intenta estrangular a su pareja con un alargador" \
  -F "highlight=intenta estrangular a su pareja" \
  -F "image_url=https://diarioeldia-s3.cdn.net.ar/s3i233/2025/10/diarioeldia/images/02/31/23/2312342_75083517659dc319fb47d1ab8d1e34cf045cf83ab0722e782cf72d14e44adf98/md.webp" \
  http://localhost:8000/generate-image-from-url
```

### Ejemplo 3: Con recorte personalizado para Instagram
```bash
curl -X POST \
  -F "headline=Mundial Sub-20: Francia vence a Noruega en un partido emocionante" \
  -F "highlight=Francia vence a Noruega" \
  -F "image_url=https://ejemplo.com/mundial-sub-20-francia-noruega.webp" \
  -F "recorte=0.14,0,0.72,1" \
  http://localhost:8000/generate-image-from-url
```

**Explicación del recorte `0.14,0,0.72,1`:**
- `0.14` = x: empieza al 14% desde la izquierda (recorta barra lateral izquierda)
- `0` = y: empieza desde arriba (sin recorte superior)
- `0.72` = w: ancho del 72% de la imagen original
- `1` = h: altura completa (100%)

Este recorte es ideal para imágenes con barras laterales o elementos no deseados en los bordes.

## Generación de Videos

### Endpoint: `/generate-video-from-url`

Genera videos en formato 9:16 (1080x1920) con efecto pan & scan cinematográfico:

```bash
curl -X POST \
  -F "headline=Cambio de mando en Carabineros: General Christian Brebi asume como nuevo Jefe" \
  -F "highlight=General Christian Brebi" \
  -F "image_url=https://ejemplo.com/imagen.jpg" \
  -F "duration=5.0" \
  -F "direction=left-to-right" \
  -F "fps=30" \
  http://localhost:8000/generate-video-from-url
```

**Parámetros del video:**
- **duration**: Duración en segundos (1-30, default: 5.0)
- **direction**: Dirección del efecto pan & scan
  - `left-to-right`: Panorámica de izquierda a derecha
  - `right-to-left`: Panorámica de derecha a izquierda
  - `top-to-bottom`: Panorámica de arriba a abajo
  - `bottom-to-top`: Panorámica de abajo a arriba
  - `zoom-in`: Zoom hacia el centro
  - `zoom-out`: Zoom desde el centro
  - `diagonal-tl-br`: Diagonal top-left a bottom-right
  - `diagonal-tr-bl`: Diagonal top-right a bottom-left
- **fps**: Cuadros por segundo (default: 30)
- **audio** *(opcional)*: Archivo de audio (mp3, wav, etc.) para agregar al video

**Respuesta:**
```json
{
  "success": true,
  "video_url": "https://thumbnail.shortenqr.com/public/videos/video_20250110_150000_abc123.mp4",
  "headline": "Cambio de mando en Carabineros: General Christian Brebi asume como nuevo Jefe",
  "highlight": "General Christian Brebi",
  "duration": 5.0,
  "direction": "left-to-right",
  "fps": 30,
  "format": "9:16",
  "dimensions": "1080x1920",
  "timestamp": "2025-01-10T15:00:01.123Z"
}
```

**Características del video:**
- ✅ Formato vertical 9:16 optimizado para Instagram Stories/Reels
- ✅ Efecto pan & scan cinematográfico sobre la imagen
- ✅ Texto overlay estático (no se mueve con la imagen)
- ✅ Mismos estilos de texto que las imágenes generadas
- ✅ Movimiento suave con easing
- ✅ Codec H.264 optimizado para web
- ✅ Soporte para audio (mp3, wav, aac, etc.)

### Ejemplo con audio:

```bash
curl -X POST \
  -F "headline=Tu titular aquí" \
  -F "highlight=texto destacado" \
  -F "image_url=https://ejemplo.com/imagen.jpg" \
  -F "duration=5.0" \
  -F "direction=zoom-in" \
  -F "audio=@/ruta/a/tu/audio.mp3" \
  http://localhost:8000/generate-video-from-url
```

El audio se ajustará automáticamente a la duración del video. Si el audio es más largo, se cortará; si es más corto, el video continuará sin audio.

## Características Técnicas

### Wrapping Inteligente
- Procesamiento carácter por carácter para preservar posiciones exactas
- Nunca corta palabras a la mitad
- Líneas de ancho variable según el contenido
- Centrado automático de cada línea

### Alineación de Texto
- Cálculo de baseline offset entre fuentes regular y bold
- Alineación vertical perfecta entre texto normal y destacado
- Preservación del espaciado original

### Compatibilidad de Fuentes
- Detección automática del sistema operativo
- Fuentes del sistema en macOS (Helvetica/Arial)
- Fallback a fuentes por defecto de PIL
- Carga automática de fuentes bold y regular

### Optimizaciones
- Cálculo conservador de anchos (75% del espacio disponible)
- Margen adicional interno (95% del espacio calculado)
- Uso de fuente bold para cálculos de ancho
- Procesamiento eficiente de imágenes grandes

## Configuración

### Configurar URL del Servidor

Edita el archivo `config.py` para cambiar la URL base:

```python
# URL base del servidor - CAMBIAR POR TU DOMINIO REAL
BASE_URL = "http://tu-dominio.com"
```

### Variables de Entorno

También puedes usar variables de entorno:

```bash
export BASE_URL="https://mi-dominio.com"
export LOG_LEVEL="debug"
```

## Estructura del Proyecto

```
imagen/
├── generate_image_api.py    # Aplicación principal FastAPI
├── config.py               # Configuración de la aplicación
├── app.py                  # Punto de entrada para producción
├── ecosystem.config.js     # Configuración de PM2
├── nginx.conf              # Configuración de Nginx
├── deploy.sh               # Script de despliegue
├── requirements.txt        # Dependencias Python
├── README.md               # Documentación
├── El_Dia.png             # Logo del diario
└── public/images/         # Directorio de imágenes generadas
```

## Dependencias

- **FastAPI**: Framework web para la API
- **Uvicorn**: Servidor ASGI
- **Pillow (PIL)**: Manipulación de imágenes
- **Requests**: Descarga de imágenes desde URLs

## Licencia

Este proyecto está bajo la Licencia MIT.

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Contacto

Para preguntas o sugerencias, por favor abre un issue en el repositorio.
