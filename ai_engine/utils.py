import PyPDF2
import io

def extraer_texto_pdf(archivo_bytes):
    """Lee un archivo PDF y devuelve su contenido en texto plano."""
    try:
        lector = PyPDF2.PdfReader(io.BytesIO(archivo_bytes))
        texto = ""
        for pagina in lector.pages:
            texto += pagina.extract_text()
        return texto.strip()
    except Exception as e:
        print(f"❌ Error leyendo PDF: {e}")
        return None