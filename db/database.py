from sqlmodel import SQLModel, create_engine, Session
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse

# 1. Cargamos tus contraseñas del .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. LA MAGIA AUTOMÁTICA: Función para crear la BD si no existe
def crear_base_datos_si_no_existe():
    print("🔍 Verificando infraestructura de la Base de Datos...")
    
    # Python desarma tu DATABASE_URL para sacar el usuario y clave automáticamente
    # Cambiamos temporalmente el prefijo para que urllib lo entienda bien
    url_limpia = DATABASE_URL.replace("postgresql+psycopg2", "postgresql")
    parsed_url = urlparse(url_limpia)
    
    db_name = parsed_url.path.lstrip("/")
    user = parsed_url.username
    password = parsed_url.password
    host = parsed_url.hostname
    port = parsed_url.port

    try:
        # Nos conectamos a la base de datos matriz 'postgres'
        conexion = psycopg2.connect(dbname="postgres", user=user, password=password, host=host, port=port)
        # Esto es obligatorio en PostgreSQL para ejecutar CREATE DATABASE
        conexion.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) 
        cursor = conexion.cursor()

        # Le preguntamos a PostgreSQL si tu base de datos ya existe
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        existe = cursor.fetchone()

        if not existe:
            print(f"🛠️ La base de datos '{db_name}' NO existe. Creándola automáticamente...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print("✨ ¡Base de datos creada con éxito!")
        else:
            print(f"👍 La base de datos '{db_name}' ya existe. Pasando a las tablas...")

        cursor.close()
        conexion.close()
        
    except Exception as e:
        print(f"❌ Error crítico al preparar la base de datos: {e}")
        exit()

# 3. Creamos el motor de conexión apuntando ya a la base de datos correcta
# Puse echo=False para que la consola no se llene de tanto código SQL y sea más limpio de leer
engine = create_engine(DATABASE_URL, echo=False)

# 4. Importamos tu modelo
from db.models import OfertaTrabajo

def crear_tablas():
    # Primero aseguramos que la "caja" (Base de datos) exista
    crear_base_datos_si_no_existe()
    
    print("⏳ Conectando y sincronizando tablas (Schema)...")
    SQLModel.metadata.create_all(engine)
    print("✅ ¡SISTEMA LISTO! Base de datos y tablas operativas.")

def obtener_sesion():
    with Session(engine) as session:
        yield session

if __name__ == "__main__":
    crear_tablas()