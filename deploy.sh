#!/bin/bash

# Script de despliegue para FastAPI Image Generator
# Uso: ./deploy.sh

set -e

echo "🚀 Iniciando despliegue de FastAPI Image Generator..."

# Variables
APP_NAME="fastapi-image-generator"
APP_DIR="/var/www/$APP_NAME"
REPO_URL="https://github.com/fcolabbe/fastapi-image-generator.git"
NGINX_SITE="fastapi-image-generator"

# Crear directorio de la aplicación si no existe
echo "📁 Creando directorio de la aplicación..."
sudo mkdir -p $APP_DIR

# Clonar o actualizar el repositorio
if [ -d "$APP_DIR/.git" ]; then
    echo "🔄 Actualizando repositorio existente..."
    cd $APP_DIR
    sudo git pull origin main
else
    echo "📥 Clonando repositorio..."
    sudo git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi

# Instalar dependencias Python
echo "📦 Instalando dependencias..."
sudo pip3 install -r requirements.txt

# Crear directorio de logs si no existe
sudo mkdir -p /var/log/pm2

# Configurar permisos
echo "🔐 Configurando permisos..."
sudo chown -R www-data:www-data $APP_DIR
sudo chmod +x $APP_DIR/app.py

# Detener la aplicación si está corriendo
echo "⏹️ Deteniendo aplicación existente..."
pm2 stop $APP_NAME 2>/dev/null || true
pm2 delete $APP_NAME 2>/dev/null || true

# Iniciar la aplicación con PM2
echo "🚀 Iniciando aplicación con PM2..."
cd $APP_DIR
pm2 start ecosystem.config.js

# Guardar configuración de PM2
pm2 save

# Configurar PM2 para iniciar al boot
pm2 startup | sudo bash

echo "✅ Aplicación desplegada exitosamente!"
echo "📊 Estado: pm2 status"
echo "📋 Logs: pm2 logs $APP_NAME"
echo "🌐 URL: http://tu-servidor/generate-image"
