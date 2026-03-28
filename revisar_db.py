from sqlmodel import Session, select
from db.database import engine
from db.models import OfertaTrabajo

def ver_resultados():
    with Session(engine) as session:
        # Traemos solo las que ya analizó la IA
        sentencia = select(OfertaTrabajo).where(OfertaTrabajo.match_score != None)
        resultados = session.exec(sentencia).all()
        
        print(f"\n📊 TOTAL ANALIZADAS: {len(resultados)}\n")
        for o in resultados:
            print(f"[{o.match_score}%] {o.titulo} en {o.empresa}")
            print(f"   💡 Razón: {o.match_reason}\n" + "-"*50)

if __name__ == "__main__":
    ver_resultados()