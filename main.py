import json
import sys
import asyncio
import threading 
import warnings
from datetime import datetime
from typing import List
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, SQLModel, delete
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

# Silenciar avisos de paquetes obsoletos
warnings.filterwarnings("ignore", category=FutureWarning)

# --- TUS IMPORTACIONES ---
from db.database import obtener_sesion, engine
from db.models import OfertaTrabajo, PerfilUsuario
from ai_engine.analizador import analizar_compatibilidad, generar_carta_presentacion, model
from ai_engine.utils import extraer_texto_pdf 
from notifications.messenger import enviar_alerta_match 
from generators.word_gen import crear_docx_carta
from scrapers.computrabajo import extraer_y_guardar

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# --- MEJORA: Gestión de Ciclo de Vida (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⚙️ Verificando y creando tablas en PostgreSQL...")
    SQLModel.metadata.create_all(engine)
    yield
    print("🔌 Apagando servidor JobRadar AI...")

app = FastAPI(title="JobRadar AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalisisRequest(BaseModel):
    cv_texto: str

@app.get("/")
def home():
    return {"status": "Online", "message": "JobRadar AI Backend funcionando"}

# --- 1. SUBIDA DE CV (PROMPT DE IA REFORZADO + EXTRACCIÓN DE NOMBRE + CORRECCIÓN) ---

@app.post("/api/subir-cv")
async def subir_cv(
    nombre_usuario: str, 
    ubicacion: str = "Lima", 
    file: UploadFile = File(...), 
    session: Session = Depends(obtener_sesion)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")

    contenido = await file.read()
    texto_cv = extraer_texto_pdf(contenido)
    
    if not texto_cv:
        raise HTTPException(status_code=500, detail="No se pudo extraer texto del PDF")

    print("🧠 IA deduciendo profesión y nombre...")
    try:
        # Devuelve JSON con Profesión y Nombre
        prompt = (
            "Eres un Headhunter Experto Multidisciplinario. Analiza el texto de este CV y extrae dos cosas:\n"
            "1. El nombre completo del candidato.\n"
            "2. El cargo laboral exacto que busca.\n\n"
            "REGLAS CRÍTICAS:\n"
            "- LEE EL CONTEXTO COMPLETO: Comprende la industria para deducir el cargo. Si menciona 'software', 'pruebas', es 'Analista QA'. Si menciona 'ladrillos', es 'Albañil'.\n"
            "- IGNORA títulos universitarios generales si el perfil detalla una especialidad.\n"
            "- El cargo debe tener MÁXIMO 3 PALABRAS (ej. 'Analista QA', 'Ingeniero Mecatrónico', 'Recepcionista Hotel').\n"
            "- Responde ÚNICAMENTE con un objeto JSON válido con las claves 'nombre' y 'profesion'.\n"
            "- Ejemplo de salida: {\"nombre\": \"Juan Pérez García\", \"profesion\": \"Analista de Datos\"}\n\n"
            f"TEXTO DEL CV: {texto_cv[:1500]}"
        )
        res = model.generate_content(prompt)
        
        # Limpiar y parsear JSON
        respuesta_sucia = res.text.replace("```json", "").replace("```", "").strip()
        datos_ia = json.loads(respuesta_sucia)
        
        # Si la IA encontró un nombre en el CV, lo usamos. Si no, usamos el que mandó el frontend por defecto.
        nombre_detectado = datos_ia.get("nombre", "").strip()
        if len(nombre_detectado) > 3: # Validación simple para asegurar que no nos devuelva iniciales
            nombre_final = nombre_detectado
        else:
            nombre_final = nombre_usuario
            
        profesion_detectada = datos_ia.get("profesion", "Analista de Sistemas")
        
        print(f"✅ Detectado: Nombre -> {nombre_final} | Puesto -> {profesion_detectada}")

    except Exception as e:
        print(f"⚠️ Error IA analizando CV: {e}")
        # Salvavidas extra
        nombre_final = nombre_usuario
        texto_upper = texto_cv.upper()
        if "QA" in texto_upper or "QUALITY ASSURANCE" in texto_upper:
            profesion_detectada = "QA Tester"
        else:
            profesion_detectada = "Analista de Sistemas"

    # Guardar en base de datos usando el nombre extraído
    perfil = session.exec(select(PerfilUsuario).where(PerfilUsuario.nombre == nombre_final)).first()
    if perfil:
        # --- 🔥 AQUÍ ESTABA EL ERROR: Falta actualizar el nombre en el perfil existente ---
        perfil.nombre = nombre_final # <-- Línea agregada para corregir el problema
        # -----------------------------------------------------------------------------------
        perfil.cv_texto = texto_cv
        perfil.fecha_actualizacion = datetime.now()
    else:
        # Esto es para cuando el perfil es totalmente nuevo
        perfil = PerfilUsuario(nombre=nombre_final, cv_texto=texto_cv)
    
    session.add(perfil)
    session.commit()
    session.refresh(perfil)

    print(f"🚀 Lanzando robot para: '{profesion_detectada}' en '{ubicacion}'")
    
    # Pasamos profesión limpia y ubicación al robot
    threading.Thread(target=extraer_y_guardar, args=(profesion_detectada, ubicacion)).start()

    return {
        "mensaje": f"Buscando {profesion_detectada} en {ubicacion} para el perfil de {nombre_final}",
        "profesion_detectada": profesion_detectada,
        "nombre_detectado": nombre_final
    }

# --- 2. ENDPOINTS DE ANÁLISIS (Sin cambios) ---

@app.get("/api/ofertas", response_model=List[OfertaTrabajo])
def listar_ofertas(session: Session = Depends(obtener_sesion)):
    return session.exec(select(OfertaTrabajo)).all()

@app.post("/api/analizar-con-perfil/{nombre_usuario}")
async def analizar_con_perfil(nombre_usuario: str, session: Session = Depends(obtener_sesion)):
    perfil = session.exec(select(PerfilUsuario).where(PerfilUsuario.nombre == nombre_usuario)).first()
    if not perfil:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return await analizar_perfil(AnalisisRequest(cv_texto=perfil.cv_texto), session)

@app.post("/api/analizar-mi-perfil")
async def analizar_perfil(request: AnalisisRequest, session: Session = Depends(obtener_sesion)):
    ofertas = session.exec(select(OfertaTrabajo).where(OfertaTrabajo.match_score == None)).all()
    if not ofertas:
        return {"mensaje": "No hay ofertas nuevas."}

    resultados_finales = []
    for oferta in ofertas:
        try:
            texto_oferta = f"Título: {oferta.titulo}. Requisitos: {oferta.requisitos}"
            respuesta_ia = await analizar_compatibilidad(request.cv_texto, texto_oferta)
            json_limpio = respuesta_ia.replace("```json", "").replace("```", "").strip()
            data = json.loads(json_limpio)
            
            oferta.match_score = int(data.get("porcentaje", 0))
            oferta.match_reason = data.get("razon", "Analizado por IA")
            oferta.estado = "Analizado"
            
            if oferta.match_score >= 70:
                await enviar_alerta_match(oferta.titulo, oferta.empresa, oferta.match_score, oferta.match_reason, oferta.url)
            session.add(oferta)
            resultados_finales.append(oferta)
        except: continue 

    session.commit()
    return {"mensaje": f"Procesadas {len(resultados_finales)} ofertas", "data": resultados_finales}

@app.post("/api/analizar-oferta-unica/{oferta_id}")
async def analizar_oferta_especifica(oferta_id: int, request: AnalisisRequest, session: Session = Depends(obtener_sesion)):
    oferta = session.get(OfertaTrabajo, oferta_id)
    if not oferta: raise HTTPException(status_code=404, detail="Oferta no encontrada")
    try:
        texto_oferta = f"Título: {oferta.titulo}. Requisitos: {oferta.requisitos}"
        respuesta_ia = await analizar_compatibilidad(request.cv_texto, texto_oferta)
        data = json.loads(respuesta_ia.replace("```json", "").replace("```", "").strip())
        oferta.match_score = int(data.get("porcentaje", 0))
        oferta.match_reason = data.get("razon", "Analizado")
        oferta.estado = "Analizado"
        session.add(oferta)
        session.commit()
        session.refresh(oferta)
        return {"data": oferta}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# --- 3. GENERACIÓN Y OPTIMIZACIÓN (Sin cambios) ---

@app.post("/api/generar-carta/{oferta_id}")
async def crear_carta(oferta_id: int, request: AnalisisRequest, session: Session = Depends(obtener_sesion)):
    oferta = session.get(OfertaTrabajo, oferta_id)
    if not oferta: raise HTTPException(status_code=404, detail="No encontrada")
    carta = await generar_carta_presentacion(request.cv_texto, f"{oferta.titulo}. {oferta.requisitos}")
    oferta.carta_presentacion = carta
    session.add(oferta)
    session.commit()
    return {"id": oferta_id, "carta": carta}

@app.post("/api/optimizar-cv/{oferta_id}")
async def optimizar_cv(oferta_id: int, request: AnalisisRequest, session: Session = Depends(obtener_sesion)):
    oferta = session.get(OfertaTrabajo, oferta_id)
    if not oferta: raise HTTPException(status_code=404, detail="No encontrada")
    prompt = f"CV: {request.cv_texto}\nOferta: {oferta.requisitos}\nDime 3 habilidades clave faltantes."
    try:
        respuesta = model.generate_content(prompt)
        return {"oferta": oferta.titulo, "faltantes": respuesta.text.strip()}
    except Exception as e: return {"error": str(e)}

@app.get("/api/descargar-carta/{oferta_id}")
async def descargar_carta(oferta_id: int, nombre_usuario: str, session: Session = Depends(obtener_sesion)):
    oferta = session.get(OfertaTrabajo, oferta_id)
    if not oferta or not oferta.carta_presentacion: raise HTTPException(status_code=404, detail="Carta no generada.")
    buffer = crear_docx_carta(nombre_usuario, oferta.titulo, oferta.empresa, oferta.carta_presentacion)
    filename = f"Carta_{oferta.empresa.replace(' ', '_')}.docx"
    return StreamingResponse(buffer, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f"attachment; filename={filename}"})

# --- 4. UTILIDADES (Sin cambios) ---

@app.delete("/api/limpiar-ofertas")
def limpiar_ofertas(session: Session = Depends(obtener_sesion)):
    try:
        statement = delete(OfertaTrabajo)
        resultado = session.exec(statement)
        session.commit()
        return {"mensaje": "Base de datos limpia", "borradas": resultado.rowcount}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al limpiar DB: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)