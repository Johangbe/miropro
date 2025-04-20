from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json, time, base64
import urllib.parse

def decodificar_enlace(enlace_ofuscado):
    try:
        # Extraer lo que está después de ?r=
        if "?r=" in enlace_ofuscado:
            base64_str = enlace_ofuscado.split("?r=")[1]
            decoded = base64.b64decode(base64_str).decode()
            return decoded
    except:
        return None
    return None

def construir_embed_url(enlace_decodificado):
    if not enlace_decodificado:
        return None
    if "stream=" in enlace_decodificado:
        canal = urllib.parse.parse_qs(urllib.parse.urlparse(enlace_decodificado).query).get("stream", [""])[0]
        return f"https://futbollibre.net/embed/{canal}.html"
    return enlace_decodificado

def scroll_dentro_iframe(page):
    iframe_element = page.query_selector("iframe[src*='agenda']")
    iframe = iframe_element.content_frame()
    prev_height = 0
    for _ in range(30):
        iframe.evaluate("window.scrollBy(0, 500)")
        time.sleep(1)
        new_height = iframe.evaluate("document.documentElement.scrollHeight")
        if new_height == prev_height:
            break
        prev_height = new_height
    return iframe.content()

def extraer_desde_html(html):
    soup = BeautifulSoup(html, "html.parser")
    partidos = []

    for partido_li in soup.select("ul.menu > li"):
        a_tag = partido_li.find("a")
        if not a_tag or not a_tag.text:
            continue

        hora_tag = a_tag.find("span", class_="t")
        hora = hora_tag.text.strip() if hora_tag else ""

        texto = a_tag.text.replace(hora, "").strip() if hora else a_tag.text.strip()
        if ":" in texto:
            competencia, equipos = map(str.strip, texto.split(":", 1))
        else:
            competencia, equipos = "Desconocido", texto

        canales = []
        for canal_li in partido_li.select("ul > li.subitem1"):
            canal_a = canal_li.find("a")
            if canal_a:
                nombre = canal_a.contents[0].strip() if canal_a.contents else "Desconocido"
                calidad_tag = canal_a.find("span")
                calidad = calidad_tag.text.strip() if calidad_tag else "Desconocido"
                enlace_ofuscado = canal_a.get("href", "")
                enlace_decodificado = decodificar_enlace(enlace_ofuscado)
                embed_final = construir_embed_url(enlace_decodificado)

                canales.append({
                    "nombre": nombre,
                    "calidad": calidad,
                    "enlace": embed_final or enlace_ofuscado
                })

        partidos.append({
            "hora": hora,
            "competición": competencia,
            "equipos": equipos,
            "canales": canales
        })

    return partidos

def scrape_y_extraer_agenda():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://librefutbol.su", wait_until="load")

        try:
            page.wait_for_selector("iframe[src*='agenda']", timeout=20000)
        except Exception as e:
            print("No se detectó el iframe:", e)
            browser.close()
            return

        print("Scrolleando dentro del iframe...")
        html = scroll_dentro_iframe(page)

        browser.close()

    partidos = extraer_desde_html(html)

    with open("agenda_resultado.json", "w", encoding="utf-8") as f:
        json.dump(partidos, f, ensure_ascii=False, indent=4)

    print("¡Agenda guardada como agenda_resultado.json!")

# Ejecutar todo
scrape_y_extraer_agenda()
