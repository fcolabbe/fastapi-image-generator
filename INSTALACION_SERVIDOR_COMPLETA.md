# 🚀 Instalación Completa en Servidor Nuevo

## 📋 Requisitos del Servidor
- **RAM mínima**: 2GB (recomendado 4GB para videos largos)
- **CPU**: 2 cores mínimo
- **Disco**: 20GB mínimo
- **OS**: Ubuntu 22.04 o 24.04

---

## 1️⃣ Preparación Inicial

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    git \
    nginx \
    ffmpeg \
    fonts-dejavu-core \
    fonts-liberation

# Instalar Node.js y PM2
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

# Verificar instalaciones
python3 --version
node --version
pm2 --version
ffmpeg -version
```

---

## 2️⃣ Clonar y Configurar Proyecto

```bash
# Crear directorio y clonar
sudo mkdir -p /var/www
cd /var/www
sudo git clone https://github.com/fcolabbe/fastapi-image-generator.git
cd fastapi-image-generator

# Configurar Git (para futuros pulls)
sudo git config --global --add safe.directory /var/www/fastapi-image-generator

# Crear virtual environment
python3 -m venv venv

# Activar venv e instalar dependencias
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Crear directorios públicos
sudo mkdir -p public/images public/videos
sudo chmod -R 755 public/
```

---

## 3️⃣ Configurar PM2

```bash
cd /var/www/fastapi-image-generator

# Iniciar con PM2
pm2 start ecosystem.config.js

# Guardar configuración para que inicie al reiniciar servidor
pm2 save
pm2 startup

# Verificar que está corriendo
pm2 status
pm2 logs fastapi-image-generator --lines 20
```

**Archivo `ecosystem.config.js`** (ya está en el repo):
```javascript
module.exports = {
  apps: [{
    name: 'fastapi-image-generator',
    script: 'venv/bin/uvicorn',
    args: 'generate_image_api:app --host 0.0.0.0 --port 8000',
    cwd: '/var/www/fastapi-image-generator',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    error_file: '/var/log/pm2/fastapi-image-generator-error.log',
    out_file: '/var/log/pm2/fastapi-image-generator-out.log',
    log_file: '/var/log/pm2/fastapi-image-generator-combined.log',
    time: true
  }]
}
```

---

## 4️⃣ Configurar Nginx

```bash
# Crear configuración de Nginx
sudo tee /etc/nginx/sites-available/fastapi-image-generator > /dev/null << 'EOF'
# Configuración de Nginx para FastAPI Image Generator
server {
    listen 80;
    server_name thumbnail.shortenqr.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name thumbnail.shortenqr.com;
    
    ssl_certificate /etc/letsencrypt/live/thumbnail.shortenqr.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/thumbnail.shortenqr.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    access_log /var/log/nginx/fastapi-image-generator.access.log;
    error_log /var/log/nginx/fastapi-image-generator.error.log;
    
    # Servir archivos estáticos (imágenes y videos)
    location /public/ {
        alias /var/www/fastapi-image-generator/public/;
        expires 1d;
        add_header Cache-Control "public, immutable";
        access_log off;
        
        location ~ \.(mp4|webm|ogg)$ {
            add_header Content-Type video/mp4;
            add_header Accept-Ranges bytes;
        }
    }
    
    # Proxy a FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts para videos largos (5 minutos)
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        client_max_body_size 100M;
        client_body_timeout 300s;
        
        # Buffers
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # Headers de seguridad
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Compresión
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;
}
EOF

# Activar configuración
sudo ln -sf /etc/nginx/sites-available/fastapi-image-generator /etc/nginx/sites-enabled/

# Agregar timeouts globales en nginx.conf
sudo sed -i '/http {/a\    # Timeouts globales\n    client_body_timeout 300s;\n    client_header_timeout 300s;\n    keepalive_timeout 300s;\n    send_timeout 300s;' /etc/nginx/nginx.conf

# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## 5️⃣ Configurar SSL con Let's Encrypt

```bash
# Instalar certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado SSL (sustituye el dominio)
sudo certbot --nginx -d thumbnail.shortenqr.com

# Verificar renovación automática
sudo certbot renew --dry-run

# Ver cuando expira
sudo certbot certificates
```

---

## 6️⃣ Configurar Firewall

```bash
# Habilitar UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # FastAPI (opcional, solo para debug)
sudo ufw enable

# Verificar
sudo ufw status
```

---

## 7️⃣ Verificación Final

```bash
# Verificar que todo está corriendo
pm2 status
sudo systemctl status nginx
sudo netstat -tulpn | grep -E ':(80|443|8000)'

# Ver logs en tiempo real
pm2 logs fastapi-image-generator

# Test local (desde el servidor)
curl http://localhost:8000/
curl http://localhost:8000/docs

# Test desde fuera (desde tu Mac)
curl https://thumbnail.shortenqr.com/
```

---

## 8️⃣ Comandos Útiles para Mantenimiento

### Actualizar código desde GitHub
```bash
cd /var/www/fastapi-image-generator
sudo git pull origin main
pm2 restart fastapi-image-generator
```

### Ver logs
```bash
# Logs de FastAPI (PM2)
pm2 logs fastapi-image-generator
pm2 logs fastapi-image-generator --lines 100

# Logs de Nginx
sudo tail -f /var/log/nginx/fastapi-image-generator.access.log
sudo tail -f /var/log/nginx/fastapi-image-generator.error.log
```

### Reiniciar servicios
```bash
# Reiniciar FastAPI
pm2 restart fastapi-image-generator

# Reiniciar Nginx
sudo systemctl restart nginx

# Reiniciar todo
pm2 restart all
sudo systemctl restart nginx
```

### Verificar memoria y CPU
```bash
free -h
htop
df -h
pm2 monit
```

### Limpiar archivos generados (opcional)
```bash
# Borrar imágenes antiguas (más de 7 días)
find /var/www/fastapi-image-generator/public/images -type f -mtime +7 -delete

# Borrar videos antiguos (más de 7 días)
find /var/www/fastapi-image-generator/public/videos -type f -mtime +7 -delete
```

---

## 9️⃣ Test Completo de Funcionalidad

### Desde tu Mac, prueba estos endpoints:

**1. Generar imagen horizontal + Instagram (4:5):**
```bash
curl -X POST -s \
  -F "headline=Prueba de titular largo para verificar que no se corten palabras" \
  -F "highlight=palabras" \
  -F "image_url=https://media.biobiochile.cl/wp-content/uploads/2025/10/e-e-u-u--enviara-a-sobrevivientes-de-submarino-siniestrado-a-colombia-y-ecuador-sus-paises-de-origen.png" \
  https://thumbnail.shortenqr.com/generate-image-from-url | python3 -m json.tool
```

**2. Generar video sin audio:**
```bash
curl -X POST -s \
  -F "headline=Video de prueba sin audio" \
  -F "highlight=sin audio" \
  -F "image_url=https://media.biobiochile.cl/wp-content/uploads/2025/10/e-e-u-u--enviara-a-sobrevivientes-de-submarino-siniestrado-a-colombia-y-ecuador-sus-paises-de-origen.png" \
  -F "direction=zoom-in" \
  -F "keep_aspect=true" \
  -F "duration=5.0" \
  https://thumbnail.shortenqr.com/generate-video-from-url | python3 -m json.tool
```

**3. Generar video con audio (archivo local):**
```bash
curl -X POST --max-time 240 -s \
  -F "headline=Video con audio de prueba" \
  -F "highlight=con audio" \
  -F "image_url=https://media.biobiochile.cl/wp-content/uploads/2025/10/e-e-u-u--enviara-a-sobrevivientes-de-submarino-siniestrado-a-colombia-y-ecuador-sus-paises-de-origen.png" \
  -F "direction=zoom-in" \
  -F "keep_aspect=true" \
  -F "audio=@tu_audio.wav" \
  https://thumbnail.shortenqr.com/generate-video-from-url | python3 -m json.tool
```

---

## 🔟 Troubleshooting

### Problema: 502 Bad Gateway
```bash
# Verificar que FastAPI esté corriendo
pm2 status
pm2 logs fastapi-image-generator --lines 50

# Verificar timeouts de Nginx
grep "proxy_read_timeout" /etc/nginx/sites-available/fastapi-image-generator
grep "client_body_timeout" /etc/nginx/nginx.conf

# Reiniciar todo
pm2 restart fastapi-image-generator
sudo systemctl restart nginx
```

### Problema: Videos con audio fallan
```bash
# Verificar memoria disponible
free -h

# Ver si FastAPI crashea por memoria
pm2 logs fastapi-image-generator --lines 100 | grep -i "killed\|memory\|error"

# Aumentar límite de memoria en PM2 (editar ecosystem.config.js)
# Cambiar: max_memory_restart: '2G'
```

### Problema: Permisos en archivos generados
```bash
# Dar permisos a directorios públicos
sudo chmod -R 755 /var/www/fastapi-image-generator/public/
sudo chown -R www-data:www-data /var/www/fastapi-image-generator/public/
```

### Problema: Git no actualiza
```bash
cd /var/www/fastapi-image-generator
sudo git status
sudo git stash
sudo git pull origin main
sudo git stash pop
pm2 restart fastapi-image-generator
```

---

## ✅ Checklist de Instalación

- [ ] Sistema actualizado
- [ ] Python 3.12 instalado
- [ ] Node.js y PM2 instalados
- [ ] FFmpeg instalado
- [ ] Repositorio clonado en `/var/www/fastapi-image-generator`
- [ ] Virtual environment creado
- [ ] Dependencias de Python instaladas
- [ ] Directorios `public/images` y `public/videos` creados
- [ ] PM2 configurado y corriendo
- [ ] Nginx configurado con timeouts correctos
- [ ] SSL configurado con Let's Encrypt
- [ ] Firewall (UFW) configurado
- [ ] Tests funcionando correctamente

---

## 📞 URLs de Prueba

- **Documentación API**: https://thumbnail.shortenqr.com/docs
- **Health check**: https://thumbnail.shortenqr.com/
- **Ejemplo imagen**: https://thumbnail.shortenqr.com/public/images/
- **Ejemplo video**: https://thumbnail.shortenqr.com/public/videos/

---

## 📝 Notas Importantes

1. **Memoria**: Para videos largos (>20 segundos con audio), se recomienda al menos 2GB de RAM
2. **Storage**: Limpia archivos antiguos regularmente para no llenar el disco
3. **Backups**: Considera hacer backup de `/var/www/fastapi-image-generator/public/` si necesitas conservar los archivos generados
4. **Logs**: Los logs de PM2 crecen con el tiempo, considera rotarlos
5. **SSL**: Let's Encrypt renueva automáticamente cada 90 días

---

## 🎯 Resumen Rápido

```bash
# Instalación rápida (script completo)
sudo apt update && sudo apt install -y python3.12 python3.12-venv git nginx ffmpeg nodejs npm
sudo npm install -g pm2
cd /var/www && sudo git clone https://github.com/fcolabbe/fastapi-image-generator.git
cd fastapi-image-generator
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
sudo mkdir -p public/{images,videos}
pm2 start ecosystem.config.js && pm2 save && pm2 startup

# Configurar Nginx (copiar el bloque del paso 4)
# Configurar SSL: sudo certbot --nginx -d thumbnail.shortenqr.com

# ¡Listo! 🚀
```

