# 🚀 Instalación en Servidor de Desarrollo

Guía paso a paso para desplegar FastAPI Image Generator en tu servidor usando PM2 y Nginx.

## 📋 Prerrequisitos

- Servidor Ubuntu/Debian
- Acceso root o sudo
- Python 3.8+
- Node.js y NPM (para PM2)
- Nginx

## 🔧 Instalación de Dependencias

### 1. Actualizar el sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Python y dependencias
```bash
sudo apt install python3 python3-pip python3-venv -y
```

### 3. Instalar Node.js y NPM
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 4. Instalar PM2 globalmente
```bash
sudo npm install -g pm2
```

### 5. Instalar Nginx
```bash
sudo apt install nginx -y
```

## 🚀 Despliegue de la Aplicación

### 1. Ejecutar el script de despliegue
```bash
# Desde tu máquina local, copia los archivos al servidor
scp -r /Users/fcolabbe/Downloads/imagen/ usuario@tu-servidor:/tmp/

# En el servidor
cd /tmp/imagen
chmod +x deploy.sh
sudo ./deploy.sh
```

### 2. Configurar Nginx

```bash
# Copiar configuración de Nginx
sudo cp nginx.conf /etc/nginx/sites-available/fastapi-image-generator

# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/fastapi-image-generator /etc/nginx/sites-enabled/

# Remover sitio por defecto
sudo rm /etc/nginx/sites-enabled/default

# Probar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 3. Configurar firewall (opcional)
```bash
# Permitir HTTP y HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

## 🔍 Verificación del Despliegue

### 1. Verificar estado de PM2
```bash
pm2 status
pm2 logs fastapi-image-generator
```

### 2. Verificar Nginx
```bash
sudo systemctl status nginx
sudo nginx -t
```

### 3. Probar la API
```bash
# Test básico
curl http://localhost:8000/docs

# Test con imagen (desde el servidor)
curl -X POST \
  -F "headline=Test desde servidor: Aplicación funcionando correctamente" \
  -F "highlight=funcionando correctamente" \
  -F "image_url=https://diarioeldia-s3.cdn.net.ar/s3i233/2025/10/diarioeldia/images/02/31/23/2312395_6bfbb9a763f2750c48d613bd27b191339e04f4dc2c7eeb675fc27762fa4373e3/md.webp" \
  http://localhost:8000/generate-image-from-url \
  --output test_servidor.png
```

## 📊 Comandos Útiles

### PM2
```bash
# Ver estado de todas las aplicaciones
pm2 status

# Ver logs en tiempo real
pm2 logs fastapi-image-generator --lines 100

# Reiniciar aplicación
pm2 restart fastapi-image-generator

# Detener aplicación
pm2 stop fastapi-image-generator

# Monitoreo
pm2 monit
```

### Nginx
```bash
# Recargar configuración
sudo nginx -s reload

# Ver logs
sudo tail -f /var/log/nginx/fastapi-image-generator.access.log
sudo tail -f /var/log/nginx/fastapi-image-generator.error.log

# Probar configuración
sudo nginx -t
```

### Sistema
```bash
# Ver uso de recursos
htop
df -h
free -h

# Ver puertos en uso
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :80
```

## 🔄 Actualizaciones

### Actualizar la aplicación
```bash
cd /var/www/fastapi-image-generator
sudo git pull origin main
sudo pip3 install -r requirements.txt
pm2 restart fastapi-image-generator
```

### Actualizar configuración de Nginx
```bash
sudo nano /etc/nginx/sites-available/fastapi-image-generator
sudo nginx -t
sudo systemctl reload nginx
```

## 🛠️ Troubleshooting

### Problema: PM2 no inicia la aplicación
```bash
# Ver logs detallados
pm2 logs fastapi-image-generator --err

# Verificar dependencias
cd /var/www/fastapi-image-generator
python3 -c "import fastapi, uvicorn, PIL, requests; print('Todas las dependencias OK')"
```

### Problema: Nginx no puede conectar
```bash
# Verificar que la app esté corriendo
pm2 status
curl http://localhost:8000/docs

# Verificar configuración de Nginx
sudo nginx -t
```

### Problema: Permisos de archivos
```bash
# Corregir permisos
sudo chown -R www-data:www-data /var/www/fastapi-image-generator
sudo chmod +x /var/www/fastapi-image-generator/app.py
```

## 📈 Monitoreo y Logs

### Logs importantes:
- **PM2**: `/var/log/pm2/fastapi-image-generator.log`
- **Nginx Access**: `/var/log/nginx/fastapi-image-generator.access.log`
- **Nginx Error**: `/var/log/nginx/fastapi-image-generator.error.log`
- **Sistema**: `/var/log/syslog`

### Monitoreo en tiempo real:
```bash
# Logs de la aplicación
pm2 logs fastapi-image-generator --lines 0

# Logs de Nginx
sudo tail -f /var/log/nginx/fastapi-image-generator.access.log

# Monitoreo de sistema
htop
```

## 🔒 Configuración de SSL (Opcional)

Para producción, considera usar Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d tu-dominio.com
```

## ✅ Checklist Final

- [ ] Aplicación corriendo en PM2
- [ ] Nginx configurado y funcionando
- [ ] API respondiendo en http://tu-servidor/docs
- [ ] Generación de imágenes funcionando
- [ ] Logs configurados
- [ ] Firewall configurado
- [ ] Monitoreo activo

¡Tu FastAPI Image Generator está listo para producción! 🎉
