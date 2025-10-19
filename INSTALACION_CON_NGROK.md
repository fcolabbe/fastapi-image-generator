# 🚀 Instalación con ngrok (Sin dominio propio)

## 📋 Requisitos
- **RAM**: 2GB mínimo (4GB recomendado para videos largos)
- **CPU**: 2 cores mínimo
- **OS**: Ubuntu 22.04 o 24.04
- **Cuenta ngrok**: Gratis en https://ngrok.com

---

## 1️⃣ Instalación Base

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    git \
    ffmpeg \
    fonts-dejavu-core \
    fonts-liberation \
    curl \
    unzip

# Instalar Node.js y PM2
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2
```

---

## 2️⃣ Clonar Proyecto

```bash
# Crear directorio y clonar
sudo mkdir -p /var/www
cd /var/www
sudo git clone https://github.com/fcolabbe/fastapi-image-generator.git
cd fastapi-image-generator

# Configurar Git
sudo git config --global --add safe.directory /var/www/fastapi-image-generator

# Crear virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Crear directorios públicos
sudo mkdir -p public/images public/videos
sudo chmod -R 755 public/
```

---

## 3️⃣ Instalar y Configurar ngrok

```bash
# Descargar ngrok
cd ~
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update
sudo apt install ngrok

# Verificar instalación
ngrok version
```

**Autenticarse en ngrok:**

1. Ve a https://dashboard.ngrok.com/get-started/your-authtoken
2. Copia tu authtoken
3. Ejecuta:

```bash
ngrok config add-authtoken TU_AUTHTOKEN_AQUI
```

---

## 4️⃣ Configurar config.py para ngrok

Edita el archivo de configuración:

```bash
cd /var/www/fastapi-image-generator
nano config.py
```

**IMPORTANTE**: Deja `BASE_URL` vacío por ahora, lo actualizaremos después:

```python
"""
Configuración centralizada para la aplicación
"""

# URL base del servidor (se actualizará con la URL de ngrok)
BASE_URL = "http://localhost:8000"  # Temporal

# Directorios locales (no cambian con ngrok)
PUBLIC_IMAGES_DIR = "/var/www/fastapi-image-generator/public/images"
PUBLIC_VIDEOS_DIR = "/var/www/fastapi-image-generator/public/videos"

# Rutas URL para archivos públicos
IMAGES_URL_PATH = "/public/images"
VIDEOS_URL_PATH = "/public/videos"
```

---

## 5️⃣ Iniciar FastAPI con PM2

```bash
cd /var/www/fastapi-image-generator

# Iniciar con PM2
pm2 start ecosystem.config.js

# Guardar configuración
pm2 save
pm2 startup

# Verificar que está corriendo
pm2 status
pm2 logs fastapi-image-generator --lines 20
```

---

## 6️⃣ Iniciar ngrok con PM2

**Crear configuración de ngrok para PM2:**

```bash
cd /var/www/fastapi-image-generator
nano ecosystem.ngrok.config.js
```

**Contenido:**

```javascript
module.exports = {
  apps: [{
    name: 'ngrok-tunnel',
    script: 'ngrok',
    args: 'http 8000 --log=stdout',
    autorestart: true,
    watch: false,
    error_file: '/var/log/pm2/ngrok-error.log',
    out_file: '/var/log/pm2/ngrok-out.log',
    log_file: '/var/log/pm2/ngrok-combined.log',
    time: true
  }]
}
```

**Iniciar ngrok con PM2:**

```bash
pm2 start ecosystem.ngrok.config.js
pm2 save

# Ver la URL pública de ngrok
pm2 logs ngrok-tunnel --lines 50 | grep -i "url="
```

O también puedes ver la URL en: http://localhost:4040 (si tienes acceso al servidor con navegador)

---

## 7️⃣ Obtener y Configurar URL de ngrok

**Opción 1: Desde los logs de PM2**

```bash
pm2 logs ngrok-tunnel --lines 100 --nostream | grep "url="
```

Verás algo como:
```
url=https://abc123.ngrok-free.app
```

**Opción 2: API de ngrok**

```bash
curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])"
```

**Actualizar config.py con la URL de ngrok:**

```bash
# Obtener URL automáticamente
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null || echo "")

echo "URL de ngrok: $NGROK_URL"

# Actualizar config.py
cd /var/www/fastapi-image-generator
sed -i "s|BASE_URL = \".*\"|BASE_URL = \"$NGROK_URL\"|" config.py

# Reiniciar FastAPI para que tome los cambios
pm2 restart fastapi-image-generator
```

---

## 8️⃣ Script de Actualización Automática de URL

Crea un script para actualizar la URL automáticamente cuando ngrok reinicie:

```bash
nano /var/www/fastapi-image-generator/update_ngrok_url.sh
```

**Contenido:**

```bash
#!/bin/bash
# Script para actualizar automáticamente la URL de ngrok en config.py

CONFIG_FILE="/var/www/fastapi-image-generator/config.py"
MAX_RETRIES=10
RETRY_DELAY=3

echo "🔄 Esperando que ngrok esté listo..."

for i in $(seq 1 $MAX_RETRIES); do
    # Intentar obtener la URL de ngrok
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)
    
    if [ ! -z "$NGROK_URL" ]; then
        echo "✅ URL de ngrok obtenida: $NGROK_URL"
        
        # Actualizar config.py
        sed -i "s|BASE_URL = \".*\"|BASE_URL = \"$NGROK_URL\"|" $CONFIG_FILE
        
        echo "📝 config.py actualizado"
        
        # Reiniciar FastAPI
        pm2 restart fastapi-image-generator
        
        echo "🚀 FastAPI reiniciado con nueva URL"
        echo ""
        echo "🌐 Tu API está disponible en: $NGROK_URL"
        echo "📖 Documentación: $NGROK_URL/docs"
        
        exit 0
    fi
    
    echo "⏳ Intento $i/$MAX_RETRIES - Esperando $RETRY_DELAY segundos..."
    sleep $RETRY_DELAY
done

echo "❌ No se pudo obtener la URL de ngrok después de $MAX_RETRIES intentos"
exit 1
```

**Hacer ejecutable:**

```bash
chmod +x /var/www/fastapi-image-generator/update_ngrok_url.sh
```

**Ejecutar:**

```bash
/var/www/fastapi-image-generator/update_ngrok_url.sh
```

---

## 9️⃣ Verificación Final

```bash
# Ver todos los servicios
pm2 status

# Ver URL actual
pm2 logs ngrok-tunnel --lines 20 | grep "url="

# Ver config actual
grep "BASE_URL" /var/www/fastapi-image-generator/config.py

# Test local
curl http://localhost:8000/

# Ver la URL pública completa
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])")
echo "🌐 API pública: $NGROK_URL"
echo "📖 Docs: $NGROK_URL/docs"
```

---

## 🔟 Probar desde tu Mac

```bash
# Primero obtén la URL de ngrok desde el servidor
# Luego prueba:

# Reemplaza NGROK_URL con tu URL real
NGROK_URL="https://abc123.ngrok-free.app"

# Test básico
curl $NGROK_URL/

# Test de imagen
curl -X POST -s \
  -F "headline=Test con ngrok" \
  -F "highlight=con ngrok" \
  -F "image_url=https://media.biobiochile.cl/wp-content/uploads/2025/10/e-e-u-u--enviara-a-sobrevivientes-de-submarino-siniestrado-a-colombia-y-ecuador-sus-paises-de-origen.png" \
  $NGROK_URL/generate-image-from-url | python3 -m json.tool

# Test de video
curl -X POST --max-time 120 -s \
  -F "headline=Video de prueba" \
  -F "highlight=de prueba" \
  -F "image_url=https://media.biobiochile.cl/wp-content/uploads/2025/10/e-e-u-u--enviara-a-sobrevivientes-de-submarino-siniestrado-a-colombia-y-ecuador-sus-paises-de-origen.png" \
  -F "direction=zoom-in" \
  -F "keep_aspect=true" \
  -F "duration=3.0" \
  $NGROK_URL/generate-video-from-url | python3 -m json.tool
```

---

## 📝 Comandos Útiles

### Ver URL de ngrok
```bash
curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])"
```

### Actualizar URL después de reinicio de ngrok
```bash
/var/www/fastapi-image-generator/update_ngrok_url.sh
```

### Ver logs
```bash
# FastAPI
pm2 logs fastapi-image-generator

# ngrok
pm2 logs ngrok-tunnel

# Ambos
pm2 logs
```

### Reiniciar servicios
```bash
# Reiniciar todo
pm2 restart all

# Solo FastAPI
pm2 restart fastapi-image-generator

# Solo ngrok
pm2 restart ngrok-tunnel
```

### Actualizar código
```bash
cd /var/www/fastapi-image-generator
sudo git pull origin main
pm2 restart fastapi-image-generator
```

---

## ⚠️ Limitaciones de ngrok (Plan Gratuito)

1. **URL cambia**: Cada vez que reinicies ngrok, la URL cambia
2. **Límite de conexiones**: 40 conexiones/minuto
3. **Página de advertencia**: ngrok muestra una página de advertencia la primera vez
4. **Sin SSL personalizado**: No puedes usar tu propio dominio

### Solución para URL que cambia:

**Opción 1: ngrok con dominio fijo (Plan de pago)**
```bash
ngrok http 8000 --domain=tu-subdominio.ngrok-free.app
```

**Opción 2: Script automático en inicio**

Agrega esto al final de `ecosystem.config.js`:

```javascript
{
  name: 'update-ngrok-url',
  script: '/var/www/fastapi-image-generator/update_ngrok_url.sh',
  autorestart: false,
  watch: false
}
```

---

## 🔒 Mejoras de Seguridad (Opcional)

### 1. Agregar autenticación básica en ngrok

Crea `~/.ngrok2/ngrok.yml`:

```yaml
authtoken: TU_AUTHTOKEN
tunnels:
  fastapi:
    proto: http
    addr: 8000
    auth: "usuario:contraseña"
```

Inicia con:
```bash
ngrok start fastapi
```

### 2. Limitar IPs permitidas (solo con plan de pago)

---

## ✅ Checklist de Instalación

- [ ] Servidor con 2GB+ RAM
- [ ] Python, Node.js, PM2, FFmpeg instalados
- [ ] Repositorio clonado
- [ ] Dependencias de Python instaladas
- [ ] ngrok instalado y autenticado
- [ ] FastAPI corriendo con PM2
- [ ] ngrok corriendo con PM2
- [ ] URL de ngrok obtenida
- [ ] `config.py` actualizado con URL de ngrok
- [ ] Tests funcionando desde fuera

---

## 🆘 Troubleshooting

### ngrok no inicia
```bash
# Ver logs
pm2 logs ngrok-tunnel

# Verificar autenticación
ngrok config check

# Reiniciar
pm2 restart ngrok-tunnel
```

### URL no se actualiza
```bash
# Ejecutar script manualmente
/var/www/fastapi-image-generator/update_ngrok_url.sh

# Ver config actual
cat /var/www/fastapi-image-generator/config.py | grep BASE_URL
```

### "502 Bad Gateway" desde ngrok
```bash
# Verificar que FastAPI esté corriendo
pm2 status
curl http://localhost:8000/

# Reiniciar FastAPI
pm2 restart fastapi-image-generator
```

### Videos con audio fallan
```bash
# Verificar RAM
free -h

# Si tienes <2GB, aumenta la RAM del servidor
```

---

## 📊 Monitoreo

```bash
# Ver estado general
pm2 monit

# Ver memoria
free -h

# Ver uso de disco
df -h

# Ver procesos
htop
```

---

## 🎯 Resumen Ultra Rápido

```bash
# 1. Instalar todo
sudo apt update && sudo apt install -y python3.12 python3.12-venv git ffmpeg nodejs npm
sudo npm install -g pm2

# 2. Instalar ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
ngrok config add-authtoken TU_AUTHTOKEN

# 3. Clonar y configurar
cd /var/www && sudo git clone https://github.com/fcolabbe/fastapi-image-generator.git
cd fastapi-image-generator
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && deactivate
sudo mkdir -p public/{images,videos}

# 4. Iniciar servicios
pm2 start ecosystem.config.js
pm2 start ecosystem.ngrok.config.js
pm2 save && pm2 startup

# 5. Actualizar URL
chmod +x update_ngrok_url.sh
./update_ngrok_url.sh

# 6. Ver URL
curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])"
```

---

**¡Listo! Tu API está pública con ngrok.** 🎉

**Recuerda**: La URL de ngrok cambia cada vez que reinicies. Usa el script `update_ngrok_url.sh` para actualizarla automáticamente.

