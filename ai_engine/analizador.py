import google.generativeai as genai
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Leer las llaves del .env y convertirlas en una lista limpia
raw_keys = os.getenv("GEMINI_API_KEYS", "")
API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]

if not API_KEYS:
    raise ValueError("❌ No se encontraron API Keys en el archivo .env")

current_key_index = 0

def configurar_siguiente_key():
    global current_key_index, model
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    nueva_key = API_KEYS[current_key_index]
    
    genai.configure(api_key=nueva_key)
    # Re-instanciamos el modelo con la nueva configuración
    model = genai.GenerativeModel('gemini-2.5-flash')
    print(f"🔄 Cuota agotada. Rotando a API Key #{current_key_index + 1}")

# Configuración inicial con la primera llave
genai.configure(api_key=API_KEYS[0])
model = genai.GenerativeModel('gemini-2.5-flash')

async def analizar_compatibilidad(cv_texto, oferta_texto):
    global model
    prompt = f"""
    Analiza la compatibilidad. Responde solo JSON:
    {{"porcentaje": 0, "razon": ""}}
    CV: {cv_texto[:2000]}
    Oferta: {oferta_texto[:2000]}
    """
    
    # Intentar con cada llave disponible si falla por cuota
    for _ in range(len(API_KEYS)):
        try:
            # Usamos to_thread porque la librería de Google es bloqueante
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text
        except Exception as e:
            if "429" in str(e):
                configurar_siguiente_key()
            else:
                print(f"❌ Error inesperado en IA: {e}")
                raise e
                
    return '{"porcentaje": 0, "razon": "Límite de cuota excedido en todas las llaves."}'

async def generar_carta_presentacion(cv_texto, oferta_texto):
    prompt = f"Escribe una carta de presentación corta para: {oferta_texto[:1000]} basada en: {cv_texto[:1000]}"
    try:
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text
    except:
        return "No se pudo generar la carta (Límite de API)."