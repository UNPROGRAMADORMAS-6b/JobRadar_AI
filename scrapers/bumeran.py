import time
import random
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError
from sqlmodel import Session, select
from db.database import engine
from db.models import OfertaTrabajo

def extraer_y_guardar_bumeran(termino_busqueda: str, ubicacion: str = "Lima"):
    print(f"🟣 [ROBOT BUMERAN] Iniciando búsqueda para: '{termino_busqueda}' en '{ubicacion}'...")
    datos_extraidos = []

    with sync_playwright() as p:
        navegador = p.chromium.launch(
            headless=False, # Ponlo en True si no quieres ver cómo se abre la ventana
            slow_mo=random.randint(50, 150),
            args=["--disable-blink-features=AutomationControlled", "--window-size=1366,768"]
        )
        
        contexto = navegador.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        pagina = contexto.new_page()
        pagina.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            # 1. Ir a Bumeran Perú
            pagina.goto("https://www.bumeran.com.pe/", wait_until="domcontentloaded", timeout=40000)
            
            # Cerrar popups molestos si aparecen
            try:
                pagina.click("button:has-text('Entendido')", timeout=2000)
            except:
                pass

            # 2. Escribir el cargo
            print("🟣 [BUMERAN] Escribiendo búsqueda...")
            # Bumeran suele usar un input con placeholder que contiene "Puesto" o "palabra clave"
            input_cargo = pagina.locator("input[placeholder*='Puesto'], input[placeholder*='palabra clave']").first
            input_cargo.wait_for(timeout=10000)
            input_cargo.click()
            input_cargo.fill(termino_busqueda)
            time.sleep(random.uniform(1.0, 2.0))
            
            # En Bumeran, al presionar Enter en el primer input suele buscar directo
            pagina.keyboard.press("Enter")
            
            # Esperar a que carguen los resultados (buscamos enlaces que lleven a un aviso)
            pagina.wait_for_selector("a[href*='/empleos/']", timeout=15000)
            time.sleep(3) # Pausa extra para que termine de renderizar React

            # 3. Extraer Ofertas (Solo la primera página para ser rápidos)
            print("🟣 [BUMERAN] Leyendo vitrina de ofertas...")
            
            # Bumeran carga las tarjetas como divs gigantes que envuelven un enlace (a)
            tarjetas = pagina.locator("a[href*='/empleos/']").all()
            
            for tarjeta in tarjetas:
                try:
                    href = tarjeta.get_attribute("href")
                    # Filtrar enlaces que no son de ofertas directas
                    if not href or "-aviso-" not in href:
                        continue
                        
                    # Extraer el título del H2 o H3 dentro del enlace
                    try:
                        titulo = tarjeta.locator("h2, h3").first.inner_text(timeout=1000).strip()
                    except:
                        titulo = "Título no encontrado"
                        
                    url = f"https://www.bumeran.com.pe{href}" if href.startswith("/") else href
                    
                    # Intentamos sacar la empresa y un resumen del texto visible
                    texto_completo = tarjeta.inner_text().split('\n')
                    texto_limpio = [t.strip() for t in texto_completo if t.strip()]
                    
                    empresa = "Empresa Confidencial (Bumeran)"
                    requisitos = "Detalles en Bumeran."
                    
                    if len(texto_limpio) > 1:
                        # Usualmente la empresa está justo debajo del título
                        if texto_limpio[0] == titulo:
                            empresa = texto_limpio[1]
                        
                        # Guardamos todo el texto como resumen
                        requisitos = " | ".join(texto_limpio[:5])

                    # Evitar duplicados
                    if titulo != "Título no encontrado" and url not in [d["url"] for d in datos_extraidos]:
                        print(f"🔍 [BUMERAN] Leído: {titulo[:30]}...")
                        datos_extraidos.append({
                            "titulo": titulo, 
                            "url": url,
                            "empresa": empresa,
                            "requisitos": requisitos[:1500]
                        })
                except Exception as e:
                    pass
                    
        except PlaywrightTimeoutError:
            print(f"⚠️ [BUMERAN] No se encontraron ofertas de '{termino_busqueda}' (Timeout).")
            navegador.close()
            return

        print(f"🟣 [BUMERAN] Se recolectaron {len(datos_extraidos)} ofertas en Bumeran.")

    # 4. Guardado en DB
    if datos_extraidos:
        with Session(engine) as session:
            contador_nuevos = 0
            for d in datos_extraidos:
                existente = session.exec(select(OfertaTrabajo).where(OfertaTrabajo.url == d["url"])).first()
                if not existente:
                    session.add(OfertaTrabajo(
                        titulo=d["titulo"], 
                        empresa=d.get("empresa", "Confidencial"),
                        url=d["url"], 
                        requisitos=d.get("requisitos", "Detalles en web"), 
                        estado="Nuevo"
                    ))
                    contador_nuevos += 1
            session.commit()
            print(f"🎉 ¡Robot Bumeran terminó! Guardadas {contador_nuevos} ofertas nuevas.")