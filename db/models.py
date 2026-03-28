from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class OfertaTrabajo(SQLModel, table=True):
    # --- IDENTIFICACIÓN ---
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # --- DATOS DE LA OFERTA ---
    titulo: str
    empresa: str
    salario: str = Field(default="No especificado")
    requisitos: str = Field(default="")
    url: str = Field(unique=True)
    
    # --- FECHAS ---
    fecha_extraccion: datetime = Field(default_factory=datetime.now)
    
    # --- INTELIGENCIA ARTIFICIAL (IA) ---
    match_score: Optional[int] = Field(default=None)
    match_reason: Optional[str] = Field(default=None)
    estado: str = Field(default="Pendiente")
    
    # --- GENERACIÓN DE DOCUMENTOS ---
    carta_presentacion: Optional[str] = Field(default=None)

# --- NUEVA TABLA PARA PERSISTENCIA ---
class PerfilUsuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True) # Para identificar al usuario (ej: "principal")
    cv_texto: str                   # Aquí guardaremos el texto extraído del PDF
    fecha_actualizacion: datetime = Field(default_factory=datetime.now)