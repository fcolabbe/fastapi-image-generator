# 🚀 Instalación Rápida - Servidor Nuevo

## Requisitos Mínimos
- **RAM**: 2GB (mínimo 1GB, pero limitará videos largos)
- **CPU**: 2 cores
- **OS**: Ubuntu 22.04 o 24.04
- **Dominio**: Apuntando al servidor

---

## Opción 1: Instalación Automática (Recomendada)

En tu **servidor nuevo**, ejecuta:

```bash
curl -fsSL https://raw.githubusercontent.com/fcolabbe/fastapi-image-generator/main/install.sh | bash
```

Esto instalará:
- ✅ Python 3.12 + dependencias
- ✅ Node.js + PM2
- ✅ FFmpeg
- ✅ Nginx
- ✅ La aplicación en `/var/www/fastapi-image-generator`

---

## Opción 2: Instalación Manual

```bash
# 1. Instalar dependencias
sudo apt update
sudo apt install -y python3.12 python3.12-venv git nginx ffmpeg nodejs npm
sudo npm install -g pm2

# 2. Clonar proyecto
cd /var/www
sudo git clone https://github.com/fcolabbe/fastapi-image-generator.git
cd fastapi-image-generator

# 3. Instalar Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

# 4. Crear directorios
sudo mkdir -p public/{images,videos}

# 5. Iniciar con PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

## Después de Instalar: Configurar Nginx

**1. Crear configuración:**

```bash
sudo nano /etc/nginx/sites-available/fastapi-image-generator
```

**2. Pegar esta configuración** (cambia `thumbnail.shortenqr.com` por tu dominio):

```nginx
server {
    listen 80;
    server_name thumbnail.shortenqr.com;
    
    location /public/ {
        alias /var/www/fastapi-image-generator/public/;
        expires 1d;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Timeouts para videos largos
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        client_max_body_size 100M;
    }
}
```

**3. Activar y verificar:**

```bash
# Activar configuración
sudo ln -s /etc/nginx/sites-available/fastapi-image-generator /etc/nginx/sites-enabled/

# Agregar timeouts globales
sudo sed -i '/http {/a\    client_body_timeout 300s;\n    client_header_timeout 300s;\n    keepalive_timeout 300s;\n    send_timeout 300s;' /etc/nginx/nginx.conf

# Verificar y reiniciar
sudo nginx -t
sudo systemctl restart nginx
```

---

## Configurar SSL (HTTPS)

```bash
# Instalar certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado (cambia el dominio)
sudo certbot --nginx -d thumbnail.shortenqr.com

# Verificar renovación automática
sudo certbot renew --dry-run
```

---

## Verificar que Todo Funciona

**1. En el servidor:**
```bash
pm2 status
curl http://localhost:8000/
```

**2. Desde tu Mac:**
```bash
# Test básico
curl https://thumbnail.shortenqr.com/

# Test de imagen
curl -X POST -s \
  -F "headline=Test de instalación" \
  -F "highlight=instalación" \
  -F "image_url=https://media.biobiochile.cl/wp-content/uploads/2025/10/e-e-u-u--enviara-a-sobrevivientes-de-submarino-siniestrado-a-colombia-y-ecuador-sus-paises-de-origen.png" \
  https://thumbnail.shortenqr.com/generate-image-from-url | python3 -m json.tool
```

---

## Actualizar Código desde GitHub

```bash
cd /var/www/fastapi-image-generator
sudo git pull origin main
pm2 restart fastapi-image-generator
```

---

## Ver Logs

```bash
# Logs de la app
pm2 logs fastapi-image-generator

# Logs de Nginx
sudo tail -f /var/log/nginx/error.log
```

---

## Comandos Útiles

```bash
# Ver estado
pm2 status

# Reiniciar app
pm2 restart fastapi-image-generator

# Ver memoria
free -h
pm2 monit

# Limpiar archivos antiguos (>7 días)
find /var/www/fastapi-image-generator/public -type f -mtime +7 -delete
```

---

## ⚠️ Troubleshooting

### 502 Bad Gateway
```bash
pm2 logs fastapi-image-generator --lines 50
sudo systemctl status nginx
```

### Videos con audio fallan
- Verificar RAM: `free -h`
- Si tienes <2GB, los videos largos pueden fallar
- Solución: Upgrade a 2GB de RAM

### Permisos
```bash
sudo chmod -R 755 /var/www/fastapi-image-generator/public/
```

---

## 📚 Documentación Completa

Para instalación detallada paso a paso, ver: **[INSTALACION_SERVIDOR_COMPLETA.md](INSTALACION_SERVIDOR_COMPLETA.md)**

---

## ✅ Checklist

- [ ] Servidor con 2GB+ RAM
- [ ] Dominio apuntando al servidor
- [ ] Instalación completada
- [ ] PM2 corriendo (`pm2 status`)
- [ ] Nginx configurado
- [ ] SSL configurado
- [ ] Tests funcionando

---

**¡Listo! Tu servidor está configurado.** 🎉

