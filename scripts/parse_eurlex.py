#!/usr/bin/env python3
"""
Parser EUR-Lex: parsea el HTML consolidado del TUE o TFUE y genera el JSON
para load_ley.py.

El HTML de EUR-Lex tiene una estructura diferente al BOE:
  - <p class="ti-section-1"> → número de título ("TÍTULO I")
  - <p class="ti-section-2"> → denominación del título ("DISPOSICIONES COMUNES")
  - <p class="ti-art">       → encabezado de artículo ("Artículo 1")
  - <p class="sti-art">      → referencia cruzada ("(antiguo artículo 1 TUE)")
  - <p class="normal">       → párrafos de contenido
  - <p class="doc-ti">       → título de sección ("PROTOCOLOS", "DECLARACIONES")

URLs:
  TUE:  https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:12016M/TXT
  TFUE: https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:12016E/TXT

Uso:
  python3 scripts/parse_eurlex.py TUE --output data/leyes/tue.json
  python3 scripts/parse_eurlex.py TFUE --output data/leyes/tfue.json
  python3 scripts/parse_eurlex.py --file tue.html TUE --output tue.json
  python3 scripts/parse_eurlex.py TUE --output tue.json --include-protocols
  python3 scripts/parse_eurlex.py TUE --debug
"""

import re
import sys
import json
import argparse
from datetime import date

import requests
from bs4 import BeautifulSoup

# ── Metadatos conocidos ───────────────────────────────────────────────────────

LEYES_CONOCIDAS = {
    "TUE": {
        "codigo":         "TUE",
        "nombre":         "Tratado de la Unión Europea (versión consolidada 2016)",
        "nombre_corto":   "TUE",
        "tipo":           "tratado_internacional",
        "numero_oficial": "Tratado de la Unión Europea, firmado en Maastricht el 7 de febrero de 1992",
        "fecha_pub":      "2016-06-07",
        "url_boe":        None,
        "url_eli":        "https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:12016M/TXT",
        "url":            "https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:12016M/TXT",
    },
    "TFUE": {
        "codigo":         "TFUE",
        "nombre":         "Tratado de Funcionamiento de la Unión Europea (versión consolidada 2016)",
        "nombre_corto":   "TFUE",
        "tipo":           "tratado_internacional",
        "numero_oficial": "Tratado de Funcionamiento de la Unión Europea, firmado en Roma el 25 de marzo de 1957",
        "fecha_pub":      "2016-06-07",
        "url_boe":        None,
        "url_eli":        "https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:12016E/TXT",
        "url":            "https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:12016E/TXT",
    },
}

# Palabras clave que marcan el inicio de secciones no principales
PATRON_PROTOCOLO = re.compile(
    r"^(PROTOCOLO|PROTOCOLOS|DECLARACI|ANEJAS|TABLAS DE CORRESPOND)",
    re.IGNORECASE,
)

# ── Utilidades ────────────────────────────────────────────────────────────────

def _texto(tag) -> str:
    return " ".join(tag.get_text().split())


def _normalizar_titulo_num(raw: str) -> str | None:
    """
    'TÍTULO I' → 'I', 'TITULO VI' → 'VI'.
    Devuelve None si el elemento no es un título principal
    (e.g., 'Capítulo 1', 'SECCIÓN 1', números sueltos).
    """
    raw = raw.strip()
    upper = raw.upper()
    for prefijo in ("TÍTULO ", "TITULO "):
        if upper.startswith(prefijo):
            return raw[len(prefijo):].strip()
    return None  # Capítulos, Secciones y números sueltos se ignoran como títulos


def _num_articulo(raw: str) -> str:
    """'Artículo 1' → '1', 'Artículo 1 bis' → '1 bis'"""
    m = re.match(r"Art[íi]culo\s+(.+)", raw, re.IGNORECASE)
    return m.group(1).strip() if m else raw.strip()


# ── Parser principal ──────────────────────────────────────────────────────────

def parsear(soup: BeautifulSoup, include_protocols: bool = False, debug: bool = False):
    """
    Recorre el HTML de EUR-Lex en orden documental y extrae:
      - titulos, capitulos (vacío si no hay), artículos
    Devuelve (titulos, capitulos, articulos).
    """
    titulos = []
    capitulos = []  # EUR-Lex TUE/TFUE usa secciones pero no capítulos formales
    articulos = []

    titulo_orden = 0
    art_orden = 0

    # Estado actual
    en_protocolos = False
    titulo_num_actual = None
    titulo_den_actual = None
    titulo_num_pendiente = None  # ti-section-1 visto, esperando ti-section-2

    titulos_vistos: set[str] = set()

    def _guardar_titulo_si_nuevo():
        nonlocal titulo_orden
        if titulo_num_actual and titulo_num_actual not in titulos_vistos:
            titulo_orden += 1
            titulos.append({
                "numero":       titulo_num_actual,
                "denominacion": titulo_den_actual or titulo_num_actual,
                "orden":        titulo_orden,
            })
            titulos_vistos.add(titulo_num_actual)

    # Artículo en construcción
    art_num_actual = None
    art_contenido_parrafos: list[str] = []

    def _cerrar_articulo():
        nonlocal art_orden
        if art_num_actual is not None:
            contenido = "\n".join(art_contenido_parrafos).strip()
            if contenido:
                articulos.append({
                    "numero":          art_num_actual,
                    "tipo":            "articulo",
                    "contenido":       contenido,
                    "titulo_numero":   titulo_num_actual,
                    "capitulo_numero": None,
                    "seccion_numero":  None,
                    "orden_global":    art_orden,
                })
                art_orden += 1

    # Recorrer todos los elementos en orden documental
    for tag in soup.find_all(["p", "div"]):
        clases = tag.get("class") or []
        cls = clases[0] if clases else ""
        texto = _texto(tag)

        if not texto:
            continue

        # ── Detección de sección protocolo/declaración ──
        if cls == "doc-ti":
            if PATRON_PROTOCOLO.match(texto):
                if not include_protocols:
                    if debug:
                        print(f"[STOP] Detectado inicio de protocolos: {texto[:80]}")
                    _cerrar_articulo()
                    break
                else:
                    # Nuevo bloque de protocolo: cerrar artículo en curso y registrar pseudo-título
                    en_protocolos = True
                    _cerrar_articulo()
                    art_num_actual = None
                    art_contenido_parrafos = []
                    titulo_num_actual = texto[:50]
                    titulo_den_actual = texto
                    titulo_num_pendiente = None
                    _guardar_titulo_si_nuevo()
            continue

        # ── Título (número) — solo si empieza por TÍTULO/TITULO ──
        if cls == "ti-section-1":
            num = _normalizar_titulo_num(texto)
            if num is not None:
                _cerrar_articulo()
                art_num_actual = None
                art_contenido_parrafos = []
                # Actualizar titulo_num_actual ya aquí: cualquier ti-art que aparezca
                # antes del ti-section-2 correspondiente quedará bajo el título correcto.
                titulo_num_actual = num
                titulo_den_actual = num  # denominación provisional hasta que llegue ti-section-2
                titulo_num_pendiente = num
                if debug:
                    print(f"[TIT-NUM] {titulo_num_pendiente}")
            else:
                if debug:
                    print(f"[SKIP ti-section-1] {texto[:60]}")
            continue

        # ── Título (denominación) ──
        if cls == "ti-section-2":
            if titulo_num_pendiente:
                titulo_den_actual = texto  # actualiza la denominación provisional
                _guardar_titulo_si_nuevo()
                titulo_num_pendiente = None
                if debug:
                    print(f"[TIT-DEN] {titulo_num_actual}: {titulo_den_actual[:60]}")
            continue

        # ── Artículo (encabezado) ──
        if cls == "ti-art":
            _cerrar_articulo()
            art_num_actual = _num_articulo(texto)
            art_contenido_parrafos = []
            if debug:
                print(f"[ART] {art_num_actual} (título={titulo_num_actual})")
            continue

        # ── Sub-artículo (referencia cruzada, incluir como contexto) ──
        if cls == "sti-art" and art_num_actual:
            art_contenido_parrafos.append(f"[{texto}]")
            continue

        # ── Contenido de artículo ──
        if cls == "normal" and art_num_actual:
            art_contenido_parrafos.append(texto)
            continue

    # Cerrar el último artículo
    _cerrar_articulo()

    # Eliminar artículos duplicados (mismo número + mismo título)
    vistos: set[tuple] = set()
    arts_unicos = []
    for a in articulos:
        clave = (a["numero"], a["titulo_numero"])
        if clave not in vistos:
            vistos.add(clave)
            arts_unicos.append(a)
    # Re-numerar orden_global
    for i, a in enumerate(arts_unicos, 1):
        a["orden_global"] = i

    return titulos, capitulos, arts_unicos


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Parsea el HTML de EUR-Lex (TUE/TFUE) y genera JSON para load_ley.py")
    parser.add_argument("codigo",
                        help="Código de la ley: TUE, TFUE, o cualquier código personalizado")
    parser.add_argument("--url",
                        help="URL de EUR-Lex (si no se especifica, se usa la URL conocida para TUE/TFUE)")
    parser.add_argument("--file",
                        help="Fichero HTML local en lugar de descargar")
    parser.add_argument("--output", "-o", required=True,
                        help="Fichero JSON de salida")
    parser.add_argument("--include-protocols", action="store_true",
                        help="Incluir protocolos y declaraciones (por defecto se excluyen)")
    parser.add_argument("--nombre",
                        help="Nombre completo de la ley (si no es TUE/TFUE)")
    parser.add_argument("--nombre-corto",
                        help="Nombre corto")
    parser.add_argument("--fecha-pub", default="2016-06-07",
                        help="Fecha de publicación (YYYY-MM-DD)")
    parser.add_argument("--debug", action="store_true",
                        help="Imprimir estructura detectada")
    args = parser.parse_args()

    codigo = args.codigo.upper()

    # Metadatos de la ley
    if codigo in LEYES_CONOCIDAS:
        meta = LEYES_CONOCIDAS[codigo].copy()
    else:
        if not args.nombre:
            parser.error(f"Para código '{codigo}' desconocido debes indicar --nombre")
        meta = {
            "codigo":         codigo,
            "nombre":         args.nombre,
            "nombre_corto":   args.nombre_corto or codigo,
            "tipo":           "tratado_internacional",
            "numero_oficial": args.nombre,
            "fecha_pub":      args.fecha_pub,
            "url_boe":        None,
            "url_eli":        args.url,
            "url":            args.url,
        }

    if args.nombre:
        meta["nombre"] = args.nombre
    if args.nombre_corto:
        meta["nombre_corto"] = args.nombre_corto

    # Obtener HTML
    if args.file:
        print(f"Leyendo HTML desde: {args.file}")
        with open(args.file, encoding="utf-8") as f:
            html = f.read()
    else:
        url = args.url or meta.get("url")
        if not url:
            parser.error("Indica --url o usa un código conocido (TUE, TFUE)")
        print(f"Descargando: {url}")
        r = requests.get(url, timeout=60, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Accept-Language": "es-ES,es;q=0.9",
        })
        r.raise_for_status()
        r.encoding = "utf-8"
        html = r.text

    print("Parseando HTML...")
    soup = BeautifulSoup(html, "html.parser")
    titulos, capitulos, articulos = parsear(
        soup,
        include_protocols=args.include_protocols,
        debug=args.debug,
    )

    print(f"  Títulos:   {len(titulos)}")
    print(f"  Capítulos: {len(capitulos)}")
    print(f"  Artículos: {len(articulos)}")

    if not articulos:
        print("ADVERTENCIA: no se encontraron artículos. Comprueba el HTML con --debug.")
        sys.exit(1)

    # Construir JSON de salida
    salida = {
        "ley":       {k: v for k, v in meta.items() if k != "url"},
        "titulos":   titulos,
        "capitulos": capitulos,
        "secciones": [],
        "articulos": articulos,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print(f"\nJSON guardado en: {args.output}")
    print(f"Siguiente paso:")
    print(f"  python3 scripts/load_ley.py {args.output} --supabase --embeddings")


if __name__ == "__main__":
    main()
