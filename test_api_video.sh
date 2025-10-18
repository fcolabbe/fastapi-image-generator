#!/bin/bash
# Script para probar el API de generación de videos

echo "🎬 Probando API de generación de videos"
echo ""

# URL del servidor (cambiar según corresponda)
SERVER_URL="https://thumbnail.shortenqr.com"
# Para local: SERVER_URL="http://localhost:8000"

echo "📡 Servidor: $SERVER_URL"
echo ""

# Test 1: Video sin audio (más rápido)
echo "=========================================="
echo "TEST 1: Video SIN audio (5 segundos)"
echo "=========================================="

curl -X POST \
  -F "headline=Argentina venció a colombia y buscará su séptima corona sub20 en la final ante Marruecos" \
  -F "highlight=buscará su séptima corona sub20" \
  -F "image_url=https://diarioeldia-s3.cdn.net.ar/s3i233/2025/10/diarioeldia/images/02/31/23/2312395_6bfbb9a763f2750c48d613bd27b191339e04f4dc2c7eeb675fc27762fa4373e3/md.webp" \
  -F "duration=5.0" \
  -F "direction=zoom-in" \
  -F "fps=30" \
  -F "keep_aspect=true" \
  $SERVER_URL/generate-video-from-url | python3 -m json.tool

echo ""
echo ""

# Test 2: Video CON audio
echo "=========================================="
echo "TEST 2: Video CON audio (duración automática)"
echo "=========================================="

curl -X POST \
  -F "headline=Argentina venció a colombia y buscará su séptima corona sub20 en la final ante Marruecos" \
  -F "highlight=buscará su séptima corona sub20" \
  -F "image_url=https://diarioeldia-s3.cdn.net.ar/s3i233/2025/10/diarioeldia/images/02/31/23/2312395_6bfbb9a763f2750c48d613bd27b191339e04f4dc2c7eeb675fc27762fa4373e3/md.webp" \
  -F "direction=left-to-right" \
  -F "fps=30" \
  -F "keep_aspect=true" \
  -F "audio=@argenta.mp3" \
  $SERVER_URL/generate-video-from-url | python3 -m json.tool

echo ""
echo ""

# Test 3: Video en formato 9:16 (vertical para redes sociales)
echo "=========================================="
echo "TEST 3: Video vertical 9:16 (Instagram/TikTok)"
echo "=========================================="

curl -X POST \
  -F "headline=Argentina venció a colombia y buscará su séptima corona sub20 en la final ante Marruecos" \
  -F "highlight=buscará su séptima corona sub20" \
  -F "image_url=https://diarioeldia-s3.cdn.net.ar/s3i233/2025/10/diarioeldia/images/02/31/23/2312395_6bfbb9a763f2750c48d613bd27b191339e04f4dc2c7eeb675fc27762fa4373e3/md.webp" \
  -F "duration=5.0" \
  -F "direction=zoom-in" \
  -F "fps=30" \
  -F "keep_aspect=false" \
  $SERVER_URL/generate-video-from-url | python3 -m json.tool

echo ""
echo "✅ Pruebas completadas"

