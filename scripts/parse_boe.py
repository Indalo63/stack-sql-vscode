#!/usr/bin/env python3
"""
Parser del BOE: descarga el texto consolidado de una ley y genera el JSON
para load_ley.py

Soporta textos consolidados en formato ELI:
  https://www.boe.es/eli/es/l/2015/10/01/39/con      (ley ordinaria)
  https://www.boe.es/eli/es/lo/2007/03/22/3/con       (ley orgánica)
  https://www.boe.es/eli/es/rdlg/2015/10/30/5/con     (RDL)
  https://www.boe.es/eli/es/c/1978/12/27/(1)/con      (constitución)

Uso:
  # Descargar y parsear
  python3 scripts/parse_boe.py https://www.boe.es/eli/es/l/2015/10/01/39/con LPAC \\
    --nombre "Ley del Procedimiento Administrativo Común..." \\
    --nombre-corto "Ley 39/2015" \\
    --output data/leyes/lpac.json

  # Parsear HTML ya descargado
  python3 scripts/parse_boe.py --file boe_lpac.html LPAC --output data/leyes/lpac.json

  # Inspeccionar estructura sin parsear
  python3 scripts/parse_boe.py <url> CODIGO --debug
"""

import re
import sys
import json
import argparse
from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag

# ── Mapas de normalización ────────────────────────────────────────────────────

ORDINALES = {
    "primero": "I",       "primera": "I",
    "segundo": "II",      "segunda": "II",
    "tercero": "III",     "tercera": "III",
    "cuarto":  "IV",      "cuarta":  "IV",
    "quinto":  "V",       "quinta":  "V",
    "sexto":   "VI",      "sexta":   "VI",
    "séptimo": "VII",     "séptima": "VII",
    "octavo":  "VIII",    "octava":  "VIII",
    "noveno":  "IX",      "novena":  "IX",
    "décimo":  "X",       "décima":  "X",
    # 11-19
    "undécimo":     "XI",   "undécima":     "XI",
    "duodécimo":    "XII",  "duodécima":    "XII",
    "decimotercero":"XIII", "decimotercera":"XIII",
    "décimo tercero":"XIII","décimo tercera":"XIII",
    "decimocuarto": "XIV",  "decimocuarta": "XIV",
    "décimo cuarto":"XIV",  "décimo cuarta":"XIV",
    "decimoquinto": "XV",   "decimoquinta": "XV",
    "décimo quinto":"XV",   "décimo quinta":"XV",
    "decimosexto":  "XVI",  "decimosexta":  "XVI",
    "décimo sexto": "XVI",  "décimo sexta": "XVI",
    "decimoséptimo":"XVII", "decimoséptima":"XVII",
    "decimoctavo":  "XVIII","decimoctava":  "XVIII",
    "decimooctavo": "XVIII","decimooctava": "XVIII",
    "decimonoveno": "XIX",  "decimonovena": "XIX",
    # 20-30
    "vigésimo":   "XX",   "vigésima":   "XX",
    "vigésimo primero": "XXI",  "vigésimo primera": "XXI",
    "vigésimo segundo": "XXII", "vigésimo segunda": "XXII",
    "vigésimo tercero": "XXIII","vigésimo tercera": "XXIII",
    "vigésimo cuarto":  "XXIV", "vigésimo cuarta":  "XXIV",
    "vigésimo quinto":  "XXV",  "vigésimo quinta":  "XXV",
    "vigésimo sexto":   "XXVI", "vigésimo sexta":   "XXVI",
    "vigésimo séptimo": "XXVII","vigésimo séptima": "XXVII",
    "vigésimo octavo":  "XXVIII","vigésimo octava": "XXVIII",
    "vigésimo noveno":  "XXIX", "vigésimo novena":  "XXIX",
    "trigésimo":  "XXX",  "trigésima":  "XXX",
}

TIPO_LEY_MAP = {
    "/lo/":    "ley_organica",
    "/l/":     "ley_ordinaria",
    "/rdlg/":  "real_decreto_legislativo",
    "/rd/":    "real_decreto",
    "/c/":     "constitucion",
    "/om/":    "orden_ministerial",
}

TIPO_DISP = {
    "adicional":    "disposicion_adicional",
    "transitoria":  "disposicion_transitoria",
    "derogatoria":  "disposicion_derogatoria",
    "final":        "disposicion_final",
}


# ── Descarga ──────────────────────────────────────────────────────────────────

def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Accept-Language": "es-ES,es;q=0.9",
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text


# ── Extracción de texto de un bloque ─────────────────────────────────────────

def _texto_parrafos(bloque: Tag) -> str:
    """Extrae y une todos los párrafos de contenido de un bloque."""
    parrafos = bloque.find_all("p", class_=re.compile(r"parrafo|apartado|inciso"))
    if not parrafos:
        parrafos = bloque.find_all("p")
    lineas = []
    for p in parrafos:
        txt = p.get_text(" ", strip=True)
        if txt:
            lineas.append(txt)
    return "\n".join(lineas)


# ── Normalización de números ──────────────────────────────────────────────────

def _norm_titulo(texto: str) -> str:
    """'TÍTULO I' → 'I', 'TÍTULO PRELIMINAR' → 'PRELIMINAR'"""
    m = re.search(r'T[ÍI]TULO\s+(PRELIMINAR|[IVXLC]+)', texto, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return texto.strip()


def _norm_capitulo(texto: str) -> str:
    """'CAPÍTULO PRIMERO' → 'PRIMERO', 'CAPÍTULO I' → 'I'"""
    m = re.search(r'CAP[ÍI]TULO\s+(\w+)', texto, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return texto.strip()


def _norm_seccion(texto: str) -> tuple[str, str]:
    """
    'Sección 1.ª De los derechos fundamentales...' → numero='1.ª', denom='De los...'
    'Subsección 2.ª Prohibiciones de contratar'    → numero='Sub-2.ª', denom='Prohibiciones...'
    """
    # Subsección
    m = re.match(r'Subsecci[oó]n\s+(\d+\.?[aªa]?\.?|[A-Z]+)\s*[.–-]?\s*(.*)', texto, re.IGNORECASE)
    if m:
        num   = "Sub-" + m.group(1).strip().rstrip(".")
        denom = m.group(2).strip()
        return num, denom
    # Sección normal
    m = re.match(r'Secci[oó]n\s+(\d+\.?[aªa]?\.?|[A-Z]+)\s*[.–-]?\s*(.*)', texto, re.IGNORECASE)
    if m:
        num   = m.group(1).strip().rstrip(".")
        denom = m.group(2).strip()
        return num, denom
    return texto.strip(), ""


def _norm_articulo(texto: str) -> str:
    """'Artículo 14' → '14', 'Artículo 108 quáter' → '108 quáter'"""
    sufijos = r'(?:bis|ter|qu[aá]ter|quinquies|sexies|septies|octies|nonies|decies)'
    m = re.search(r'Art[ií]culo\s+([\d]+(?:\s+' + sufijos + r')?)', texto, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return texto.strip()


def _tipo_disposicion(texto: str) -> tuple[str, str]:
    """
    'Disposición adicional primera.'
    → tipo='disposicion_adicional', numero='DA-1'
    Devuelve (tipo, numero)
    """
    texto_l = texto.lower()
    for clave, tipo in TIPO_DISP.items():
        if clave in texto_l:
            # Buscar primero en el diccionario completo de ordinales (más largo primero)
            num = None
            for ord_str in sorted(ORDINALES.keys(), key=len, reverse=True):
                if ord_str in texto_l:
                    num_romano = ORDINALES[ord_str]
                    rom = {
                        "I":1,"II":2,"III":3,"IV":4,"V":5,"VI":6,"VII":7,"VIII":8,"IX":9,"X":10,
                        "XI":11,"XII":12,"XIII":13,"XIV":14,"XV":15,"XVI":16,"XVII":17,
                        "XVIII":18,"XIX":19,"XX":20,"XXI":21,"XXII":22,"XXIII":23,
                        "XXIV":24,"XXV":25,"XXVI":26,"XXVII":27,"XXVIII":28,"XXIX":29,"XXX":30,
                    }
                    num = str(rom.get(num_romano, num_romano))
                    break
            if num is None:
                # Fallback: buscar "única" o dígito
                m_ord = re.search(r'\b(única|único|[\d]+)\b', texto_l)
                if m_ord:
                    ord_raw = m_ord.group(1)
                    num = "1" if ord_raw in ("única", "único") else ord_raw
                else:
                    num = "1"

            prefijos = {
                "disposicion_adicional":   "DA",
                "disposicion_transitoria":  "DT",
                "disposicion_derogatoria":  "DD",
                "disposicion_final":        "DF",
            }
            codigo_num = prefijos[tipo] + (f"-{num}" if tipo != "disposicion_derogatoria" else "")
            return tipo, codigo_num

    return "articulo", texto.strip()


# ── Tipo de ley desde URL ELI ─────────────────────────────────────────────────

def _tipo_desde_url(url: str) -> str:
    for patron, tipo in TIPO_LEY_MAP.items():
        if patron in url:
            return tipo
    return "ley_ordinaria"


# ── Extracción de metadatos desde el HTML ────────────────────────────────────

def _extraer_metadatos(soup: BeautifulSoup, url: str) -> dict:
    meta = {}

    # Fecha de publicación desde metadatos
    meta_div = soup.find("div", class_="metadatos")
    if meta_div:
        txt = meta_div.get_text(" ", strip=True)
        m_fecha = re.search(r'de\s+(\d{2}/\d{2}/\d{4})', txt)
        if m_fecha:
            try:
                meta["fecha_pub"] = datetime.strptime(m_fecha.group(1), "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                pass
        m_ref = re.search(r'Referencia:\s*(BOE-[A-Z0-9-]+)', txt)
        if m_ref:
            meta["url_boe"] = f"https://www.boe.es/buscar/act.php?id={m_ref.group(1)}"
        m_eli = re.search(r'Permalink ELI:\s*(https?://\S+)', txt)
        if m_eli:
            meta["url_eli"] = m_eli.group(1)

    # Nombre desde el título de la página o primer heading
    titulo_tag = soup.find("title")
    if titulo_tag:
        meta["_page_title"] = titulo_tag.get_text(strip=True)

    meta["tipo"] = _tipo_desde_url(url)
    meta["url_eli"] = meta.get("url_eli", url)
    return meta


# ── Parser principal ──────────────────────────────────────────────────────────

def parsear(html: str, codigo: str, url: str = "", debug: bool = False) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    meta = _extraer_metadatos(soup, url)

    # Localizar contenedor del texto legal
    contenedor = soup.find("div", id="textoxslt") or soup.find("div", id="contenido")
    if not contenedor:
        raise ValueError("No se encontró el contenido legal en el HTML. "
                         "Verifica que la URL es un texto consolidado del BOE.")

    bloques = contenedor.find_all("div", class_="bloque")
    if debug:
        print(f"Total bloques: {len(bloques)}\n")
        for b in bloques:
            bid = b.get("id", "")
            h   = b.find(["h4", "h5"])
            cls = " ".join(h.get("class", [])) if h else "—"
            txt = h.get_text(" ", strip=True)[:70] if h else "—"
            print(f"  #{bid:25} {cls:25} {txt!r}")
        return {}

    # Resultado acumulado
    titulos:   list[dict] = []
    capitulos: list[dict] = []
    secciones: list[dict] = []
    articulos: list[dict] = []

    # Rastreo de números ya usados para deduplicar disposiciones y secciones
    _numeros_vistos: dict[tuple, int] = {}
    _secciones_vistas: dict[tuple, int] = {}  # (capitulo_numero, seccion_numero)

    # Estado del parser (contexto jerárquico actual)
    ctx_libro:    str | None = None  # "LI", "LII"... cuando la ley tiene Libros
    ctx_titulo:   str | None = None
    ctx_capitulo: str | None = None
    ctx_seccion:  str | None = None
    orden_libro    = 0
    orden_titulo   = 0
    orden_capitulo = 0
    orden_seccion  = 0
    orden_global   = 0

    for bloque in bloques:
        bid = bloque.get("id", "")

        # — Preámbulo ————————————————————————————————————————————
        if bid == "preambulo":
            texto = _texto_parrafos(bloque)
            if texto:
                orden_global += 1
                articulos.append({
                    "numero":          "PREAMBULO",
                    "tipo":            "preambulo",
                    "contenido":       texto,
                    "titulo_numero":   None,
                    "capitulo_numero": None,
                    "seccion_numero":  None,
                    "orden_global":    orden_global,
                })
            continue

        # — Firma / bloque sin contenido jurídico ————————————————
        if bid == "firma":
            continue

        h4 = bloque.find("h4")
        h5 = bloque.find("h5")

        # Clasificar el bloque por la clase del heading
        clases_h4 = " ".join(h4.get("class", [])) if h4 else ""
        clases_h5 = " ".join(h5.get("class", [])) if h5 else ""

        # — Libro (nivel sobre Título en leyes grandes como LCSP) ——
        if "libro" in clases_h4:
            libro_tag = bloque.find("h4", class_=re.compile(r"libro"))
            libro_txt = libro_tag.get_text(" ", strip=True) if libro_tag else ""
            # Extraer número romano del libro: "LIBRO PRIMERO" → "I", "LIBRO II" → "II"
            m_lib = re.search(r'(?:LIBRO\s+)?([IVXLC]+|\w+)$', libro_txt.strip(), re.IGNORECASE)
            if m_lib:
                raw = m_lib.group(1).upper()
                rom = {"PRIMERO":"I","SEGUNDO":"II","TERCERO":"III","CUARTO":"IV",
                       "QUINTO":"V","SEXTO":"VI","SÉPTIMO":"VII","OCTAVO":"VIII"}
                ctx_libro = f"L{rom.get(raw, raw)}"
            else:
                orden_libro += 1
                ctx_libro = f"L{orden_libro}"
            ctx_titulo   = None
            ctx_capitulo = None
            ctx_seccion  = None
            orden_titulo   = 0
            orden_capitulo = 0
            orden_seccion  = 0
            continue

        # — Título ————————————————————————————————————————————————
        if "titulo" in clases_h4:
            # Puede ser h4.titulo (TÍTULO PRELIMINAR) o h4.titulo_num + h4.titulo_tit
            num_tag  = bloque.find("h4", class_="titulo_num") or bloque.find("h4", class_="titulo")
            tit_tag  = bloque.find("h4", class_="titulo_tit")

            num_texto  = num_tag.get_text(" ", strip=True) if num_tag else ""
            tit_texto  = tit_tag.get_text(" ", strip=True) if tit_tag else ""

            num_tit      = _norm_titulo(num_texto)
            # Prefijo de Libro cuando existen varios libros con títulos homónimos
            ctx_titulo   = f"{ctx_libro}-{num_tit}" if ctx_libro else num_tit
            ctx_capitulo = None
            ctx_seccion  = None
            orden_titulo   += 1
            orden_capitulo  = 0
            orden_seccion   = 0

            titulos.append({
                "numero":       ctx_titulo,
                "denominacion": tit_texto or num_texto,
                "orden":        orden_titulo,
            })
            continue

        # — Capítulo ——————————————————————————————————————————————
        if "capitulo" in clases_h4:
            num_tag = bloque.find("h4", class_="capitulo_num")
            tit_tag = bloque.find("h4", class_="capitulo_tit")

            num_texto = num_tag.get_text(" ", strip=True) if num_tag else ""
            tit_texto = tit_tag.get_text(" ", strip=True) if tit_tag else ""

            ctx_capitulo = _norm_capitulo(num_texto)
            ctx_seccion  = None
            orden_capitulo += 1
            orden_seccion   = 0

            capitulos.append({
                "titulo_numero": ctx_titulo,
                "numero":        ctx_capitulo,
                "denominacion":  tit_texto or num_texto,
                "orden":         orden_capitulo,
            })
            continue

        # — Sección ———————————————————————————————————————————————
        if "seccion" in clases_h4:
            sec_texto    = h4.get_text(" ", strip=True)
            num_s, den_s = _norm_seccion(sec_texto)

            # Deduplicar secciones con mismo número dentro del mismo capítulo
            clave_s = (ctx_capitulo, num_s)
            if clave_s in _secciones_vistas:
                _secciones_vistas[clave_s] += 1
                sufijo_s = chr(ord('b') + _secciones_vistas[clave_s] - 1)
                num_s = f"{num_s}-{sufijo_s}"
            else:
                _secciones_vistas[clave_s] = 0

            ctx_seccion    = num_s
            orden_seccion += 1

            secciones.append({
                "titulo_numero":   ctx_titulo,
                "capitulo_numero": ctx_capitulo,
                "numero":          ctx_seccion,
                "denominacion":    den_s or sec_texto,
                "orden":           orden_seccion,
            })
            continue

        # — Artículo / Disposición ————————————————————————————————
        if "articulo" in clases_h5:
            h5_texto = h5.get_text(" ", strip=True)
            texto    = _texto_parrafos(bloque)
            if not texto:
                continue

            orden_global += 1

            # Detectar si es disposición o artículo ordinario
            es_disp = re.search(
                r'Disposici[oó]n\s+(adicional|transitoria|derogatoria|final)',
                h5_texto, re.IGNORECASE)

            if es_disp:
                tipo, numero = _tipo_disposicion(h5_texto)
                # Deduplicar: si (tipo, numero) ya existe, añadir sufijo -b, -c...
                clave = (tipo, numero)
                if clave in _numeros_vistos:
                    _numeros_vistos[clave] += 1
                    sufijo = chr(ord('b') + _numeros_vistos[clave] - 1)
                    numero = f"{numero}-{sufijo}"
                else:
                    _numeros_vistos[clave] = 0
                articulos.append({
                    "numero":          numero,
                    "tipo":            tipo,
                    "contenido":       texto,
                    "titulo_numero":   None,
                    "capitulo_numero": None,
                    "seccion_numero":  None,
                    "orden_global":    orden_global,
                })
            else:
                numero = _norm_articulo(h5_texto)
                articulos.append({
                    "numero":          numero,
                    "tipo":            "articulo",
                    "contenido":       texto,
                    "titulo_numero":   ctx_titulo,
                    "capitulo_numero": ctx_capitulo,
                    "seccion_numero":  ctx_seccion,
                    "orden_global":    orden_global,
                })
            continue

    # Construir resultado
    result = {
        "ley": {
            "codigo":         codigo,
            "nombre":         meta.get("_page_title", ""),
            "nombre_corto":   "",
            "tipo":           meta.get("tipo", "ley_ordinaria"),
            "numero_oficial": "",
            "fecha_pub":      meta.get("fecha_pub", ""),
            "url_boe":        meta.get("url_boe", ""),
            "url_eli":        meta.get("url_eli", url),
        },
        "titulos":   titulos,
        "capitulos": capitulos,
        "secciones": secciones,
        "articulos": articulos,
    }

    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Parsea texto consolidado del BOE y genera JSON para load_ley.py")

    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("url",    nargs="?",   help="URL ELI del BOE (texto consolidado)")
    src.add_argument("--file", metavar="F", help="Archivo HTML local del BOE")

    parser.add_argument("codigo",          help="Código único para la ley (ej: LPAC, TREBEP)")
    parser.add_argument("--nombre",        help="Nombre completo de la ley")
    parser.add_argument("--nombre-corto",  help="Nombre corto (ej: 'Ley 39/2015')")
    parser.add_argument("--tipo",          choices=[
        "constitucion","ley_organica","ley_ordinaria",
        "real_decreto_legislativo","real_decreto","orden_ministerial"],
        help="Tipo normativo (se infiere de la URL si no se indica)")
    parser.add_argument("--numero-oficial", help="Número oficial (ej: 'Ley 39/2015, de 1 de octubre')")
    parser.add_argument("--output", "-o",  help="Archivo de salida JSON (default: stdout)")
    parser.add_argument("--debug",  action="store_true",
                        help="Imprimir estructura de bloques y salir sin parsear")
    args = parser.parse_args()

    # Cargar HTML
    if args.file:
        print(f"Leyendo: {args.file}", file=sys.stderr)
        with open(args.file, encoding="utf-8") as f:
            html = f.read()
        url = ""
    else:
        print(f"Descargando: {args.url}", file=sys.stderr)
        html = fetch_html(args.url)
        url  = args.url

    # Parsear
    data = parsear(html, args.codigo, url=url, debug=args.debug)
    if args.debug:
        return

    # Aplicar overrides de CLI
    if args.nombre:
        data["ley"]["nombre"] = args.nombre
    if args.nombre_corto:
        data["ley"]["nombre_corto"] = args.nombre_corto
    if args.tipo:
        data["ley"]["tipo"] = args.tipo
    if args.numero_oficial:
        data["ley"]["numero_oficial"] = args.numero_oficial

    # Resumen
    ley = data["ley"]
    n_a = len(data["articulos"])
    n_t = len(data["titulos"])
    n_c = len(data["capitulos"])
    n_s = len(data["secciones"])
    print(f"\nResultado: {n_t} títulos | {n_c} capítulos | {n_s} secciones | {n_a} artículos/disposiciones",
          file=sys.stderr)
    print(f"Ley: {ley['nombre'] or '(sin nombre — usa --nombre)'}", file=sys.stderr)
    print(f"Fecha: {ley['fecha_pub']}", file=sys.stderr)

    # Advertir si faltan campos obligatorios
    if not ley["nombre"]:
        print("⚠  --nombre no indicado: edita el campo 'nombre' en el JSON antes de cargar.",
              file=sys.stderr)

    # Salida
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"JSON guardado en: {args.output}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
