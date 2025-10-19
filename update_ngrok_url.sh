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
        echo "═══════════════════════════════════════════════"
        echo "🌐 Tu API está disponible en:"
        echo "   $NGROK_URL"
        echo ""
        echo "📖 Documentación interactiva:"
        echo "   $NGROK_URL/docs"
        echo ""
        echo "🧪 Test rápido:"
        echo "   curl $NGROK_URL/"
        echo "═══════════════════════════════════════════════"
        
        exit 0
    fi
    
    echo "⏳ Intento $i/$MAX_RETRIES - Esperando $RETRY_DELAY segundos..."
    sleep $RETRY_DELAY
done

echo "❌ No se pudo obtener la URL de ngrok después de $MAX_RETRIES intentos"
echo ""
echo "Verifica que ngrok esté corriendo:"
echo "  pm2 status"
echo "  pm2 logs ngrok-tunnel"
exit 1

