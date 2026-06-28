"""
scripts/load_convocatoria.py

Carga la normativa de la convocatoria GACE (criterios de corrección + programa)
como una ley especial en normas.leyes/articulos con embeddings.

Cada tema del programa y cada criterio de corrección se convierte en un artículo
independiente para que el Q&A pueda responder preguntas como:
  "¿cuánto tiempo hay para el primer ejercicio?"
  "¿qué temas entran del bloque de Unión Europea?"
  "¿cómo se calcula la nota?"

Uso:
  python3 scripts/load_convocatoria.py --supabase --dry-run
  python3 scripts/load_convocatoria.py --supabase
"""

import os
import re
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_DIR  = Path(__file__).parent.parent
PDF_DIR   = Path("/mnt/c/Users/indal/OneDrive/Escritorio/gace_2025")

LEY_CODIGO     = "GACE_NORM"
LEY_NOMBRE     = "Normativa de la Oposición GACE — Criterios y Programa"
LEY_NOMBRE_CORTO = "GACE Normativa"

CRITERIOS_PDF = PDF_DIR / "criterio_correción_gace_2025.pdf"
NORMAS_PDF    = PDF_DIR / "Normas_especificas_gace_2025.pdf"

# Numerales romanos de bloque → título
BLOQUES = {
    "I":   "Organización del Estado y de la Administración Pública",
    "II":  "Unión Europea",
    "III": "Políticas públicas",
    "IV":  "Organización y gestión de recursos humanos",
    "V":   "Régimen jurídico del personal al servicio de la Administración",
    "VI":  "Gestión financiera y Seguridad Social",
}

_CABECERAS = re.compile(
    r'(MINISTERIO|SECRETARIA DE ESTADO|PARA LA TRANSFORMACI[OÓ]N|Y DE LA FUNCI[OÓ]N PÚBLICA|'
    r'COMISI[OÓ]N PERMANENTE|INSTITUTO NACIONAL|ADMINISTRACI[OÓ]N P[UÚ]BLICA).*?\n',
    re.IGNORECASE
)


def _load_supabase_secrets():
    secrets_path = BASE_DIR / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print("ERROR: .streamlit/secrets.toml no encontrado.", file=sys.stderr)
        sys.exit(1)
    secrets = {}
    for line in secrets_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            secrets[k.strip()] = v.strip().strip('"').strip("'")
    for k, v in secrets.items():
        os.environ[k] = v
    direct_host = secrets.get("DB_HOST", "")
    ref = direct_host.split(".")[1] if direct_host.startswith("db.") else ""
    if ref:
        os.environ["DB_HOST"] = "aws-1-eu-west-2.pooler.supabase.com"
        os.environ["DB_USER"] = f"postgres.{ref}"
    print(f"Supabase via Session Pooler: {os.environ['DB_HOST']}")


def _pdf_text(path: Path) -> str:
    import pdfplumber
    texto = ""
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texto += t + "\n"
    texto = _CABECERAS.sub("", texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto


# ── Parseo de criterios de corrección ────────────────────────────────────────

def parse_criterios(texto: str) -> list[dict]:
    """
    Cada criterio numerado (1. El primer ejercicio…) → artículo independiente.
    """
    # Dividir en bloques por número de criterio al inicio de línea
    partes = re.split(r'\n(?=\d+\.\s+[A-ZÁÉÍÓÚ])', texto)
    articulos = []
    for parte in partes:
        parte = parte.strip()
        m = re.match(r'^(\d+)\.\s+(.+)', parte, re.DOTALL)
        if not m:
            continue
        num = int(m.group(1))
        if num > 10:
            continue
        contenido = parte
        # Primera línea como título
        titulo = " ".join(contenido.split('\n')[0].split())[:120]
        articulos.append({
            "numero":   f"CRITERIO-{num}",
            "titulo":   titulo,
            "contenido": " ".join(contenido.split()),
        })
    return articulos


# ── Parseo del programa ───────────────────────────────────────────────────────

def parse_programa(texto: str) -> list[dict]:
    """
    Divide el programa en temas individuales.
    numero: "I.1", "II.3", etc.
    """
    # Localizar inicio del programa
    idx = texto.find("Programa.")
    if idx == -1:
        idx = texto.find("PROGRAMA")
    if idx == -1:
        print("  AVISO: No se encontró la sección 'Programa'")
        return []
    texto = texto[idx:]

    # Limpiar números de página sueltos
    texto = re.sub(r'\n\d{1,3}\n', '\n', texto)

    articulos = []
    bloque_actual = None

    # Líneas significativas
    lineas = texto.split('\n')
    i = 0
    while i < len(lineas):
        linea = lineas[i].strip()

        # Detectar cambio de bloque (numeral romano solo en la línea)
        m_bloque = re.match(
            r'^(I{1,3}|IV|V|VI|VII)\.\s*(.*)', linea
        )
        if m_bloque:
            roman = m_bloque.group(1)
            if roman in BLOQUES:
                bloque_actual = roman
            i += 1
            continue

        if bloque_actual is None:
            i += 1
            continue

        # Detectar inicio de tema: número + texto
        m_tema = re.match(r'^(\d+)\.\s+(.+)', linea)
        if m_tema and int(m_tema.group(1)) <= 30:
            num_tema = int(m_tema.group(1))
            # Acumular líneas del tema hasta el siguiente número o bloque
            contenido_lines = [linea]
            i += 1
            while i < len(lineas):
                sig = lineas[i].strip()
                if (re.match(r'^(\d+)\.\s+[A-ZÁÉÍÓÚ]', sig) or
                        re.match(r'^(I{1,3}|IV|V|VI|VII)\.\s', sig)):
                    break
                if sig:
                    contenido_lines.append(sig)
                i += 1

            contenido_raw = " ".join(" ".join(l.split()) for l in contenido_lines)
            titulo = contenido_raw[:120].rstrip(',').strip()

            articulos.append({
                "numero":   f"{bloque_actual}.{num_tema}",
                "titulo":   f"Bloque {bloque_actual} — Tema {num_tema}: {titulo}",
                "contenido": (
                    f"[Bloque {bloque_actual}: {BLOQUES.get(bloque_actual, '')}] "
                    f"Tema {num_tema}. {contenido_raw}"
                ),
            })
        else:
            i += 1

    return articulos


# ── Embedding ─────────────────────────────────────────────────────────────────

def _embed(textos: list[str]) -> list[list[float]]:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=textos,
    )
    return [r.embedding for r in resp.data]


# ── Base de datos ─────────────────────────────────────────────────────────────

def _get_or_create_ley(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT ley_id FROM normas.leyes WHERE codigo = %s", (LEY_CODIGO,)
        )
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            """INSERT INTO normas.leyes
                   (codigo, nombre, nombre_corto, tipo, fecha_pub, activa)
               VALUES (%s, %s, %s, 'orden_ministerial', '2025-12-18', TRUE)
               RETURNING ley_id""",
            (LEY_CODIGO, LEY_NOMBRE, LEY_NOMBRE_CORTO)
        )
        ley_id = cur.fetchone()[0]
        conn.commit()
        print(f"  Nueva ley creada: ley_id={ley_id}")
        return ley_id


def _save_articulo(conn, ley_id: int, art: dict, orden: int, dry_run: bool):
    if dry_run:
        return
    # Incluir el título en el contenido para que la búsqueda semántica lo encuentre
    contenido_completo = f"{art['titulo']}\n\n{art['contenido']}"
    embedding = _embed([contenido_completo])[0]
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO normas.articulos
                   (ley_id, numero, tipo, contenido, orden_global, embedding)
               VALUES (%s, %s, 'articulo', %s, %s, %s)
               ON CONFLICT (ley_id, numero, tipo) DO UPDATE
                   SET contenido    = EXCLUDED.contenido,
                       orden_global = EXCLUDED.orden_global,
                       embedding    = EXCLUDED.embedding""",
            (ley_id, art["numero"], contenido_completo, orden, str(embedding))
        )
    conn.commit()


# ── Runner ────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False):
    print("\nParseo de criterios de corrección…")
    texto_criterios = _pdf_text(CRITERIOS_PDF)
    criterios = parse_criterios(texto_criterios)
    print(f"  {len(criterios)} criterios extraídos")

    print("\nParseo del programa…")
    texto_normas = _pdf_text(NORMAS_PDF)
    temas = parse_programa(texto_normas)
    print(f"  {len(temas)} temas extraídos")

    articulos = criterios + temas
    print(f"\nTotal artículos a cargar: {len(articulos)}")

    if dry_run:
        print("\n[DRY-RUN] Muestra de los primeros 5 artículos:")
        for a in articulos[:5]:
            print(f"  {a['numero']:12} | {a['titulo'][:70]}")
        print("  …")
        print(f"\n[DRY-RUN] Total: {len(articulos)} artículos — nada guardado")
        return

    from app.db import get_connection
    with get_connection() as conn:
        ley_id = _get_or_create_ley(conn)
        print(f"\nCargando en normas.leyes ley_id={ley_id}…")

        ok = err = 0
        for i, art in enumerate(articulos, 1):
            try:
                _save_articulo(conn, ley_id, art, orden=i, dry_run=dry_run)
                print(f"  [OK]  {art['numero']:12} {art['titulo'][:60]}")
                ok += 1
            except Exception as e:
                print(f"  [ERR] {art['numero']:12} — {e}")
                err += 1

    print(f"\nCompletado: {ok} artículos cargados, {err} errores.")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Carga normativa GACE (criterios + programa) en la BD"
    )
    p.add_argument("--supabase", action="store_true",
                   help="Conectar a Supabase via Session Pooler")
    p.add_argument("--dry-run", action="store_true",
                   help="Parsea y muestra artículos sin guardar en BD")
    args = p.parse_args()

    if args.supabase:
        _load_supabase_secrets()
    else:
        os.environ.setdefault("DB_HOST",     "localhost")
        os.environ.setdefault("DB_PORT",     "5432")
        os.environ.setdefault("DB_NAME",     "stack_db")
        os.environ.setdefault("DB_USER",     "postgres")
        os.environ.setdefault("DB_PASSWORD", "postgres")

    run(dry_run=args.dry_run)
