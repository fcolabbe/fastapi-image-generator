#!/bin/bash
# Script de instalación automática con ngrok
# Uso: bash install_with_ngrok.sh TU_AUTHTOKEN_DE_NGROK

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🚀 FastAPI Image Generator - Instalación con ngrok  ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar argumento
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Debes proporcionar tu authtoken de ngrok${NC}"
    echo ""
    echo "Uso:"
    echo "  bash install_with_ngrok.sh TU_AUTHTOKEN"
    echo ""
    echo "Obtén tu authtoken en: https://dashboard.ngrok.com/get-started/your-authtoken"
    exit 1
fi

NGROK_AUTHTOKEN=$1

# Verificar RAM
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -lt 1900 ]; then
    echo -e "${YELLOW}⚠️  ADVERTENCIA: Tienes ${TOTAL_RAM}MB de RAM${NC}"
    echo -e "${YELLOW}   Se recomienda al menos 2GB para videos largos${NC}"
    echo ""
fi

# 1. Actualizar sistema
echo -e "${GREEN}📦 Actualizando sistema...${NC}"
sudo apt update -qq

# 2. Instalar dependencias base
echo -e "${GREEN}🔧 Instalando dependencias base...${NC}"
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    git \
    ffmpeg \
    fonts-dejavu-core \
    fonts-liberation \
    curl \
    unzip \
    > /dev/null 2>&1

# 3. Instalar Node.js y PM2
if ! command -v node &> /dev/null; then
    echo -e "${GREEN}📦 Instalando Node.js...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - > /dev/null 2>&1
    sudo apt install -y nodejs > /dev/null 2>&1
fi

if ! command -v pm2 &> /dev/null; then
    echo -e "${GREEN}📦 Instalando PM2...${NC}"
    sudo npm install -g pm2 > /dev/null 2>&1
fi

# 4. Instalar ngrok
if ! command -v ngrok &> /dev/null; then
    echo -e "${GREEN}🌐 Instalando ngrok...${NC}"
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list > /dev/null
    sudo apt update -qq
    sudo apt install -y ngrok > /dev/null 2>&1
fi

# Configurar authtoken
echo -e "${GREEN}🔑 Configurando ngrok...${NC}"
ngrok config add-authtoken $NGROK_AUTHTOKEN > /dev/null 2>&1

# 5. Clonar repositorio
echo -e "${GREEN}📂 Clonando repositorio...${NC}"
sudo mkdir -p /var/www
cd /var/www

if [ -d "fastapi-image-generator" ]; then
    echo -e "${YELLOW}⚠️  Directorio ya existe, actualizando...${NC}"
    cd fastapi-image-generator
    sudo git pull origin main > /dev/null 2>&1
else
    sudo git clone https://github.com/fcolabbe/fastapi-image-generator.git > /dev/null 2>&1
    cd fastapi-image-generator
fi

sudo git config --global --add safe.directory /var/www/fastapi-image-generator

# 6. Configurar Python
echo -e "${GREEN}🐍 Configurando Python...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
deactivate

# 7. Crear directorios
echo -e "${GREEN}📁 Creando directorios públicos...${NC}"
sudo mkdir -p public/images public/videos
sudo chmod -R 755 public/

# 8. Iniciar FastAPI con PM2
echo -e "${GREEN}🔄 Iniciando FastAPI...${NC}"
pm2 delete fastapi-image-generator 2>/dev/null || true
pm2 start ecosystem.config.js
pm2 save > /dev/null 2>&1

# 9. Iniciar ngrok con PM2
echo -e "${GREEN}🌐 Iniciando ngrok...${NC}"
pm2 delete ngrok-tunnel 2>/dev/null || true
pm2 start ecosystem.ngrok.config.js
pm2 save > /dev/null 2>&1

# Configurar PM2 para inicio automático
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp $HOME > /dev/null 2>&1

# 10. Esperar a que ngrok esté listo y actualizar URL
echo -e "${GREEN}⏳ Esperando que ngrok genere la URL...${NC}"
sleep 5

echo -e "${GREEN}🔄 Actualizando configuración con URL de ngrok...${NC}"
chmod +x update_ngrok_url.sh
./update_ngrok_url.sh

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           ✅ Instalación Completada!               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Obtener URL final
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null || echo "Obteniendo...")

echo -e "${BLUE}📊 Estado de los servicios:${NC}"
pm2 status

echo ""
echo -e "${BLUE}🌐 Tu API pública:${NC}"
echo -e "   ${GREEN}$NGROK_URL${NC}"
echo ""
echo -e "${BLUE}📖 Documentación interactiva:${NC}"
echo -e "   ${GREEN}$NGROK_URL/docs${NC}"
echo ""
echo -e "${YELLOW}⚠️  Nota importante:${NC}"
echo -e "   Con ngrok gratuito, la URL cambia cada vez que reinicies."
echo -e "   Ejecuta ${GREEN}./update_ngrok_url.sh${NC} para actualizarla."
echo ""
echo -e "${BLUE}📝 Comandos útiles:${NC}"
echo -e "   Ver logs:      ${GREEN}pm2 logs${NC}"
echo -e "   Ver estado:    ${GREEN}pm2 status${NC}"
echo -e "   Actualizar:    ${GREEN}cd /var/www/fastapi-image-generator && sudo git pull && pm2 restart all${NC}"
echo -e "   Ver URL:       ${GREEN}curl -s http://localhost:4040/api/tunnels | python3 -c 'import sys, json; print(json.load(sys.stdin)[\"tunnels\"][0][\"public_url\"])'${NC}"
echo ""
echo -e "${GREEN}🎉 ¡Todo listo para usar!${NC}"

