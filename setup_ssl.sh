#!/bin/bash

# Script para configurar SSL con Let's Encrypt para thumbnail.shortenqr.com

set -e

DOMAIN="thumbnail.shortenqr.com"
NGINX_SITE="fastapi-image-generator"

echo "🔒 Configurando SSL para $DOMAIN..."

# 1. Instalar Certbot si no está instalado
echo "📦 Instalando Certbot..."
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# 2. Verificar que Nginx está funcionando
echo "🌐 Verificando Nginx..."
sudo systemctl status nginx

# 3. Configurar Nginx temporalmente para HTTP
echo "⚙️ Configurando Nginx temporalmente..."
sudo cp nginx.conf /etc/nginx/sites-available/$NGINX_SITE

# Remover configuración SSL temporalmente
sudo sed -i '/listen 443/d' /etc/nginx/sites-available/$NGINX_SITE
sudo sed -i '/ssl_/d' /etc/nginx/sites-available/$NGINX_SITE

# Solo mantener el bloque HTTP
sudo sed -i '/return 301/d' /etc/nginx/sites-available/$NGINX_SITE

# Probar configuración
sudo nginx -t
sudo systemctl reload nginx

# 4. Obtener certificado SSL
echo "🔐 Obteniendo certificado SSL..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@shortenqr.com

# 5. Restaurar configuración completa de Nginx
echo "🔧 Restaurando configuración completa..."
sudo cp nginx.conf /etc/nginx/sites-available/$NGINX_SITE

# Probar configuración final
sudo nginx -t
sudo systemctl reload nginx

# 6. Configurar renovación automática
echo "🔄 Configurando renovación automática..."
sudo crontab -l | grep -v certbot || true
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# 7. Verificar certificado
echo "✅ Verificando certificado..."
sudo certbot certificates

echo "🎉 SSL configurado exitosamente para $DOMAIN"
echo "🌐 Tu aplicación está disponible en: https://$DOMAIN"
echo "📊 Documentación API: https://$DOMAIN/docs"
