import httpx
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def enviar_alerta_match(titulo, empresa, score, razon, url):
    """
    Envía un mensaje elegante a Telegram con el resultado del análisis.
    """
    # Configuramos un mensaje con formato HTML para que se vea profesional
    mensaje = (
        f"🚀 <b>¡NUEVO MATCH ENCONTRADO!</b>\n\n"
        f"💼 <b>Puesto:</b> {titulo}\n"
        f"🏢 <b>Empresa:</b> {empresa}\n"
        f"🎯 <b>Match Score:</b> <code>{score}%</code>\n\n"
        f"💡 <b>¿Por qué?:</b> {razon}\n\n"
        f"🔗 <a href='{url}'>Ver oferta completa</a>"
    )

    url_api = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "chat_id": CHAT_ID,
                "text": mensaje,
                "parse_mode": "HTML"
            }
            response = await client.post(url_api, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error enviando a Telegram: {e}")
            return False