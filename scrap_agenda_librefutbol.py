from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json, time

def scroll_dentro_iframe(page):
    iframe_element = page.query_selector("iframe[src*='agenda']")
    iframe = iframe_element.content_frame()
    prev_height = 0
    for _ in range(30):
        iframe.evaluate("window.scrollBy(0, 500)")
        time.sleep(2)
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

                original = canal_a.get("href", "")
                if "/en-vivo/" in original:
                    slug = original.strip("/").split("/")[-1]
                    enlace = f"https://futbollibre.net/embed/{slug}.html"
                else:
                    enlace = original

                canales.append({
                    "nombre": nombre,
                    "calidad": calidad,
                    "enlace": enlace
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
