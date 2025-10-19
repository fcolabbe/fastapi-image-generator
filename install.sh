#!/bin/bash
# Script de instalación automática para FastAPI Image Generator
# Uso: curl -fsSL https://raw.githubusercontent.com/fcolabbe/fastapi-image-generator/main/install.sh | bash

set -e

echo "🚀 Instalación de FastAPI Image Generator"
echo "=========================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar RAM
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -lt 1900 ]; then
    echo -e "${YELLOW}⚠️  ADVERTENCIA: Tienes ${TOTAL_RAM}MB de RAM${NC}"
    echo -e "${YELLOW}   Se recomienda al menos 2GB para videos largos${NC}"
    echo ""
fi

# 1. Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update -qq

# 2. Instalar dependencias
echo "🔧 Instalando dependencias..."
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    git \
    nginx \
    ffmpeg \
    fonts-dejavu-core \
    fonts-liberation \
    curl \
    > /dev/null 2>&1

# 3. Instalar Node.js y PM2
if ! command -v node &> /dev/null; then
    echo "📦 Instalando Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - > /dev/null 2>&1
    sudo apt install -y nodejs > /dev/null 2>&1
fi

if ! command -v pm2 &> /dev/null; then
    echo "📦 Instalando PM2..."
    sudo npm install -g pm2 > /dev/null 2>&1
fi

# 4. Clonar repositorio
echo "📂 Clonando repositorio..."
sudo mkdir -p /var/www
cd /var/www

if [ -d "fastapi-image-generator" ]; then
    echo "⚠️  Directorio ya existe, actualizando..."
    cd fastapi-image-generator
    sudo git pull origin main
else
    sudo git clone https://github.com/fcolabbe/fastapi-image-generator.git
    cd fastapi-image-generator
fi

# Configurar Git
sudo git config --global --add safe.directory /var/www/fastapi-image-generator

# 5. Crear virtual environment
echo "🐍 Configurando Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate

# 6. Crear directorios públicos
echo "📁 Creando directorios..."
sudo mkdir -p public/images public/videos
sudo chmod -R 755 public/

# 7. Configurar PM2
echo "🔄 Configurando PM2..."
pm2 delete fastapi-image-generator 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp $HOME

# 8. Verificar instalación
echo ""
echo "✅ Instalación completada!"
echo ""
echo "📊 Estado de la aplicación:"
pm2 status

echo ""
echo "🔗 Próximos pasos:"
echo "1. Configurar Nginx (ver INSTALACION_SERVIDOR_COMPLETA.md)"
echo "2. Configurar SSL con certbot"
echo "3. Actualizar el dominio en config.py"
echo ""
echo "📖 Documentación completa: /var/www/fastapi-image-generator/INSTALACION_SERVIDOR_COMPLETA.md"
echo ""
echo "🎉 ¡Todo listo!"

