#!/bin/bash
# Script para probar generación de video con audio desde el servidor

echo "🎬 Probando generación de video con audio desde localhost..."

# Descargar el audio primero
curl -s -o /tmp/trump.wav http://asistente.eldia.la/trump.wav

# Probar con curl desde el servidor (localhost)
curl -X POST \
  --max-time 240 \
  -F "headline=EE.UU. repatriará a Colombia y Ecuador a supervivientes de narcosubmarino con fentanilo" \
  -F "highlight=supervivientes de narcosubmarino" \
  -F "image_url=https://media.biobiochile.cl/wp-content/uploads/2025/10/e-e-u-u--enviara-a-sobrevivientes-de-submarino-siniestrado-a-colombia-y-ecuador-sus-paises-de-origen.png" \
  -F "direction=zoom-in" \
  -F "keep_aspect=true" \
  -F "audio=@/tmp/trump.wav" \
  http://127.0.0.1:8000/generate-video-from-url

echo ""
echo "✅ Test completado"

