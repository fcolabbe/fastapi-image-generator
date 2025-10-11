#!/bin/bash

# Script de despliegue completo para producción con SSL

set -e

DOMAIN="thumbnail.shortenqr.com"
APP_NAME="fastapi-image-generator"
APP_DIR="/var/www/$APP_NAME"
NGINX_SITE="fastapi-image-generator"

echo "🚀 Desplegando FastAPI Image Generator en producción..."

# 1. Actualizar repositorio
echo "📥 Actualizando código..."
cd $APP_DIR
sudo git fetch origin
sudo git reset --hard origin/main

# 2. Instalar/actualizar dependencias
echo "📦 Instalando dependencias..."
sudo $APP_DIR/venv/bin/pip install -r requirements.txt

# 3. Crear directorios necesarios
echo "📁 Creando directorios..."
sudo mkdir -p $APP_DIR/public/images
sudo mkdir -p /var/log/pm2

# 4. Configurar permisos
echo "🔐 Configurando permisos..."
sudo chown -R www-data:www-data $APP_DIR
sudo chmod +x $APP_DIR/app.py
sudo chmod -R 755 $APP_DIR/public/

# 5. Configurar Nginx
echo "🌐 Configurando Nginx..."
sudo cp $APP_DIR/nginx.conf /etc/nginx/sites-available/$NGINX_SITE

# Crear enlace simbólico si no existe
if [ ! -L /etc/nginx/sites-enabled/$NGINX_SITE ]; then
    sudo ln -s /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
fi

# Probar configuración
sudo nginx -t

# 6. Reiniciar servicios
echo "🔄 Reiniciando servicios..."
pm2 restart $APP_NAME
sudo systemctl reload nginx

# 7. Verificar estado
echo "📊 Verificando estado..."
pm2 status
sudo systemctl status nginx

# 8. Verificar DNS
echo "🌐 Verificando DNS..."
nslookup $DOMAIN

echo "✅ Despliegue completado!"
echo "🌐 Aplicación disponible en: https://$DOMAIN"
echo "📊 Documentación API: https://$DOMAIN/docs"
echo "🔧 Para configurar SSL, ejecuta: ./setup_ssl.sh"
