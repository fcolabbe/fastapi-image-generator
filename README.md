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
  http://localhost:8000/generate-image \
  --output resultado.png
```

#### 2. Generar imagen desde URL
```bash
curl -X POST \
  -F "headline=Título de la noticia" \
  -F "highlight=texto destacado" \
  -F "image_url=https://ejemplo.com/imagen.jpg" \
  http://localhost:8000/generate-image-from-url \
  --output resultado.png
```

## Parámetros

- **headline**: El titular completo de la noticia
- **highlight**: El texto que se destacará (debe estar contenido en el headline)
- **image**: Archivo de imagen local (para endpoint `/generate-image`)
- **image_url**: URL de la imagen (para endpoint `/generate-image-from-url`)

## Ejemplos de Uso

### Ejemplo 1: Noticia de Carabineros
```bash
curl -X POST \
  -F "headline=Cambio de mando en Carabineros: General Christian Brebi asume como nuevo Jefe de la Zona Coquimbo" \
  -F "highlight=General Christian Brebi" \
  -F "image_url=https://diarioeldia-s3.cdn.net.ar/s3i233/2025/10/diarioeldia/images/02/31/23/2312395_6bfbb9a763f2750c48d613bd27b191339e04f4dc2c7eeb675fc27762fa4373e3/md.webp" \
  http://localhost:8000/generate-image-from-url \
  --output resultado_carabineros.png
```

### Ejemplo 2: Noticia de Combarbalá
```bash
curl -X POST \
  -F "headline=Terror en Combarbalá: Sujeto intenta estrangular a su pareja con un alargador" \
  -F "highlight=intenta estrangular a su pareja" \
  -F "image_url=https://diarioeldia-s3.cdn.net.ar/s3i233/2025/10/diarioeldia/images/02/31/23/2312342_75083517659dc319fb47d1ab8d1e34cf045cf83ab0722e782cf72d14e44adf98/md.webp" \
  http://localhost:8000/generate-image-from-url \
  --output resultado_combarbala.png
```

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

## Estructura del Proyecto

```
imagen/
├── generate_image_api.py    # Aplicación principal FastAPI
├── README.md               # Documentación
├── El_Dia.png             # Logo del diario
└── resultado_*.png        # Imágenes de ejemplo generadas
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
