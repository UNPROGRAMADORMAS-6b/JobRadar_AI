from sqlmodel import Session, SQLModel, create_engine, text
from db.database import engine

def borrar_todo():
    print("🔨 Conectando a la base de datos para limpieza...")
    with Session(engine) as session:
        try:
            # Comando directo para borrar la tabla
            session.execute(text("DROP TABLE IF EXISTS ofertatrabajo CASCADE;"))
            session.commit()
            print("✅ ¡Tabla 'ofertatrabajo' eliminada con éxito!")
        except Exception as e:
            print(f"❌ Error al borrar: {e}")

if __name__ == "__main__":
    borrar_todo()