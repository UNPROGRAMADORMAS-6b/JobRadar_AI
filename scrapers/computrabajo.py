import time
import random
from playwright.sync_api import sync_playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError
from sqlmodel import Session, select
from db.database import engine
from db.models import OfertaTrabajo

def extraer_y_guardar(termino_busqueda: str, ubicacion: str = "Lima"):
    print(f"🤖 [ROBOT] Iniciando búsqueda UNIVERSAL MODO HUMANO para: '{termino_busqueda}' en '{ubicacion}'...")
    datos_extraidos = []

    with sync_playwright() as p:
        # Lanzamos con viewport de computadora de escritorio real
        navegador = p.chromium.launch(
            headless=False, 
            slow_mo=random.randint(50, 150), # Ligeramente más lento para parecer humano
            args=[
                "--disable-blink-features=AutomationControlled",
                "--window-size=1366,768"
            ]
        )
        
        contexto = navegador.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            extra_http_headers={"Accept-Language": "es-PE,es;q=0.9,en;q=0.8"}
        )
        
        pagina = contexto.new_page()

        # 🔥 Escudo Anti-Bot: Ocultar que somos Playwright
        pagina.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            # 1. Ir a la Home
            pagina.goto("https://pe.computrabajo.com/", wait_until="domcontentloaded", timeout=40000)
            
            try: 
                pagina.click("button:has-text('Aceptar')", timeout=3000)
            except: 
                pass

            # 2. Escribir como humano (tecla por tecla)
            input_cargo = "input[placeholder='Cargo o categoría']"
            pagina.wait_for_selector(input_cargo)
            pagina.type(input_cargo, termino_busqueda, delay=random.randint(50, 200)) # Escribe lento
            
            input_lugar = "input[placeholder='Lugar']"
            pagina.wait_for_selector(input_lugar)
            pagina.type(input_lugar, ubicacion, delay=random.randint(50, 200))
            
            time.sleep(random.uniform(1.5, 3.0)) # Piensa un poco antes de dar Enter
            pagina.keyboard.press("Enter")
            
            # Esperar resultados
            pagina.wait_for_selector("article.box_offer", timeout=15000)

            # 3. Aplicar Filtro de Últimos 7 Días
            try:
                print("⏳ Buscando filtro de últimos 7 días...")
                filtro_7_dias = pagina.locator("text='Últimos 7 días'").first
                if filtro_7_dias.is_visible(timeout=5000):
                    filtro_7_dias.click()
                    time.sleep(random.uniform(2.0, 4.0)) # Esperar que recargue
                    pagina.wait_for_selector("article.box_offer", timeout=15000)
                    print("✅ Filtro de 7 días aplicado.")
            except Exception:
                print("⚠️ No se encontró o falló el filtro de 7 días. Continuando con resultados generales.")

            # 4. Recorrer Paginación (Modo Humano)
            paginas_maximas = 3 # Limita cuántas páginas de ofertas quieres recorrer
            
            for num_pagina in range(1, paginas_maximas + 1):
                print(f"📄 Revisando página {num_pagina} del listado...")
                
                # Bajar con el scroll suavemente para simular lectura
                for _ in range(4):
                    pagina.mouse.wheel(0, 600)
                    time.sleep(random.uniform(0.5, 1.5))
                
                # Volver un poco arriba
                pagina.mouse.wheel(0, -1000)
                time.sleep(random.uniform(1.0, 2.0))

                # Extraer OFERTAS COMPLETAS
                articulos = pagina.locator("article.box_offer").all()
                for articulo in articulos:
                    try:
                        # Buscamos el enlace y título rápidamente (2 seg max)
                        enlace = articulo.locator("a.js-o-link")
                        titulo = enlace.inner_text(timeout=2000).strip()
                        href = enlace.get_attribute("href", timeout=2000)
                        
                        # 🔥 TÉCNICA MAESTRA MEJORADA: Rescate rápido de empresa (1 seg max)
                        try:
                            # Buscamos clases más genéricas que usa CompuTrabajo ahora
                            empresa = articulo.locator("a.fc_base, span.fc_base, p.fs16").first.inner_text(timeout=1000).strip()
                        except:
                            empresa = "Empresa Confidencial"

                        # Rescate rápido de requisitos (1 seg max)
                        try:
                            requisitos = articulo.locator("p").nth(1).inner_text(timeout=1000).strip()
                        except:
                            requisitos = "Revisar los detalles directamente en la web."
                        
                        if href:
                            href_limpio = href.split('#')[0].split('?')[0]
                            url = f"https://pe.computrabajo.com{href_limpio}" if href_limpio.startswith("/") else href_limpio
                            
                            # Evitar duplicados en la misma ejecución
                            if titulo and url not in [d["url"] for d in datos_extraidos]:
                                print(f"🔍 [VITRINA] Leído: {titulo} en {empresa}")
                                datos_extraidos.append({
                                    "titulo": titulo, 
                                    "url": url,
                                    "empresa": empresa,
                                    "requisitos": requisitos[:1500] # Resumen de requisitos
                                })
                    except Exception as e:
                        # Si falla algo crítico de esta oferta, pasa a la siguiente instantáneamente
                        pass

                # Intentar pasar a la siguiente página
                try:
                    btn_siguiente = pagina.locator("span[title='Siguiente'], a[title='Siguiente']").first
                    if btn_siguiente.is_visible() and "disabled" not in btn_siguiente.get_attribute("class", default=""):
                        print("👉 Pasando a la siguiente página...")
                        btn_siguiente.click()
                        time.sleep(random.uniform(3.0, 6.0)) # Pausa vital entre páginas
                        pagina.wait_for_selector("article.box_offer", timeout=15000)
                    else:
                        print("🛑 No hay más páginas disponibles.")
                        break
                except Exception:
                    print("🛑 Botón Siguiente no encontrado o no clickeable. Fin de paginación.")
                    break

        except PlaywrightTimeoutError:
            print(f"⚠️ [ROBOT] No se encontraron ofertas de '{termino_busqueda}' en '{ubicacion}' (Timeout).")
            navegador.close()
            return

        print(f"📋 Se recolectaron {len(datos_extraidos)} ofertas en total, guardando en DB...")

    # 5. Guardado en DB (SIN abrir una por una)
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
            print(f"🎉 ¡Robot Humano Universal terminó! Guardadas {contador_nuevos} ofertas nuevas.")
    else:
        print("🤷‍♂️ Robot terminó, pero no hubo datos extraídos para guardar.")