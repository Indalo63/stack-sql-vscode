"""
scripts/parse_official_exams.py

Parsea los exámenes oficiales GACE (PDF) y los carga en normas.preguntas_test.
Requiere haber ejecutado sql/ddl/021_preguntas_oficiales.sql en Supabase.

Uso:
  python3 scripts/parse_official_exams.py --supabase --dry-run   # prueba
  python3 scripts/parse_official_exams.py --supabase             # carga real
"""

import os
import re
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

EXAMENES = {
    "2024": {
        "examen":   "data/examenes/primer_ejercicio_gace-2024.pdf",
        "plantilla": "data/examenes/Plantilla_respuestas_primer_ejercicio_gace_2024.pdf",
        "fuente":   "oficial_2024",
        "anuladas": {90},
    },
    "2025": {
        "examen":   "data/examenes/primer_ejerccio-gace_2025.pdf",
        "plantilla": "data/examenes/Plantilla_respuestas_primer_ejercicio_gace_2025.pdf",
        "fuente":   "oficial_2025",
        "anuladas": set(),
    },
}

# Mapeo de patrones textuales → ley_id en normas.leyes
LEY_PATRONES = [
    (1,  [r"Constituci[oó]n Española"]),
    (4,  [r"Ley 39/2015", r"procedimiento administrativo com[uú]n"]),
    (7,  [r"Ley 40/2015", r"[Rr][eé]gimen [Jj]ur[ií]dico del [Ss]ector [Pp][uú]blico"]),
    (8,  [r"Estatuto B[aá]sico del Empleado P[uú]blico",
          r"RDL 5/2015", r"RDLeg 5/2015", r"RD Legislativo 5/2015",
          r"Ley del Estatuto B[aá]sico"]),
    (9,  [r"Ley 47/2003", r"[Gg]eneral [Pp]resupuestaria"]),
    (12, [r"Ley 9/2017", r"[Cc]ontratos del [Ss]ector [Pp][uú]blico"]),
]

# Patrones para extraer el número de artículo del enunciado
_RE_ARTICULO = re.compile(
    r'art[ií]culo[s]?\s+(\d+[\w]*(?:\.\d+)?(?:\s*bis)?)',
    re.IGNORECASE
)


def _load_supabase_secrets():
    secrets_path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
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


# ── Parseo de plantilla de respuestas ────────────────────────────────────────

def parse_plantilla(pdf_path: str) -> dict[int, str]:
    """Devuelve {num_pregunta: letra_correcta}. Ignora ANULADAS."""
    import pdfplumber
    texto = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texto += page.extract_text() + "\n"

    respuestas = {}
    for m in re.finditer(r'(\d+)\.\s+([a-dA-D]|ANULADA)', texto):
        num   = int(m.group(1))
        letra = m.group(2).lower()
        if letra != "anulada":
            respuestas[num] = letra
    return respuestas


# ── Parseo del examen ─────────────────────────────────────────────────────────

def parse_examen(pdf_path: str) -> list[dict]:
    """
    Extrae lista de preguntas del PDF.
    Cada pregunta: {num, pregunta, opciones: {a,b,c,d}}
    """
    import pdfplumber

    # Extraer todo el texto
    texto = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texto += page.extract_text() + "\n"

    # Eliminar cabeceras de página (ej. "2024 - GACE-L Página 1 de 12")
    texto = re.sub(r'\d{4}\s*-\s*GACE-\w+\s+P[aá]gina\s+\d+\s+de\s+\d+', '', texto)

    # Dividir en bloques de pregunta: "N. texto\na) ...\nb) ...\nc) ...\nd) ..."
    bloques = re.split(r'\n(?=\d+\.(?!\d)\s)', texto)

    preguntas = []
    for bloque in bloques:
        bloque = bloque.strip()
        if not bloque:
            continue

        # Número de pregunta
        m_num = re.match(r'^(\d+)\.\s*', bloque)
        if not m_num:
            continue
        num = int(m_num.group(1))
        if num > 105:
            continue

        # Separar enunciado de opciones: buscar primera aparición de \na)
        m_opciones = re.search(r'\n[a-d]\)', bloque)
        if not m_opciones:
            continue

        enunciado = bloque[m_num.end():m_opciones.start()].strip()
        resto = bloque[m_opciones.start():]

        # Extraer opciones
        opciones = {}
        for letra in "abcd":
            patron = rf'\n{letra}\)\s*(.*?)(?=\n[a-d]\)|\Z)'
            m_op = re.search(patron, resto, re.DOTALL)
            if m_op:
                opciones[letra] = " ".join(m_op.group(1).split())

        if len(opciones) == 4:
            preguntas.append({
                "num":      num,
                "pregunta": " ".join(enunciado.split()),
                "opciones": opciones,
            })

    return sorted(preguntas, key=lambda x: x["num"])


# ── Identificación de ley y artículo ─────────────────────────────────────────

def _identificar_ley(texto: str) -> int | None:
    for ley_id, patrones in LEY_PATRONES:
        for pat in patrones:
            if re.search(pat, texto, re.IGNORECASE):
                return ley_id
    return None


def _identificar_articulo(texto: str) -> str:
    m = _RE_ARTICULO.search(texto)
    return m.group(1).strip() if m else "S/N"


# ── Carga en BD ───────────────────────────────────────────────────────────────

def _save(pregunta: dict, convocatoria: str, fuente: str, dry_run: bool):
    if dry_run:
        return
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO normas.preguntas_test
                    (ley_id, articulo, pregunta,
                     opcion_a, opcion_b, opcion_c, opcion_d,
                     correcta, revisada, fuente, convocatoria, num_pregunta_oficial)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                pregunta.get("ley_id"),
                pregunta.get("articulo", "S/N"),
                pregunta["pregunta"],
                pregunta["opciones"]["a"],
                pregunta["opciones"]["b"],
                pregunta["opciones"]["c"],
                pregunta["opciones"]["d"],
                pregunta["correcta"],
                fuente,
                convocatoria,
                pregunta["num"],
            ))
        conn.commit()


# ── Runner ────────────────────────────────────────────────────────────────────

def run(convocatorias=None, dry_run=False):
    base = Path(__file__).parent.parent

    if convocatorias is None:
        convocatorias = list(EXAMENES.keys())

    total_ok = total_skip = total_err = 0

    for año in convocatorias:
        cfg = EXAMENES[año]
        print(f"\n{'='*60}")
        print(f"Convocatoria {año}")

        plantilla_path = str(base / cfg["plantilla"])
        examen_path    = str(base / cfg["examen"])

        print(f"  Parseando plantilla…")
        respuestas = parse_plantilla(plantilla_path)
        print(f"  {len(respuestas)} respuestas cargadas")

        print(f"  Parseando examen…")
        preguntas = parse_examen(examen_path)
        print(f"  {len(preguntas)} preguntas extraídas")

        ok = skip = err = 0
        for p in preguntas:
            num = p["num"]

            if num in cfg["anuladas"]:
                print(f"  [SKIP] P{num:>3} — ANULADA")
                skip += 1
                continue

            if num not in respuestas:
                print(f"  [SKIP] P{num:>3} — sin respuesta en plantilla")
                skip += 1
                continue

            p["correcta"] = respuestas[num]
            p["ley_id"]   = _identificar_ley(p["pregunta"])
            p["articulo"] = _identificar_articulo(p["pregunta"])

            ley_tag = f"ley_id={p['ley_id']}" if p["ley_id"] else "ley=externa"
            try:
                _save(p, año, cfg["fuente"], dry_run)
                ok += 1
                tag = "[DRY]" if dry_run else "[OK] "
                print(f"  {tag} P{num:>3} art.{p['articulo']:<8} {ley_tag}")
            except Exception as e:
                err += 1
                print(f"  [ERR] P{num:>3} — {e}")

        print(f"  Resultado: {ok} cargadas, {skip} omitidas, {err} errores")
        total_ok += ok; total_skip += skip; total_err += err

    print(f"\n{'='*60}")
    sufijo = " (DRY-RUN)" if dry_run else ""
    print(f"TOTAL{sufijo}: {total_ok} OK, {total_skip} omitidas, {total_err} errores")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Carga preguntas oficiales GACE en la BD")
    p.add_argument("--supabase", action="store_true",
                   help="Conectar a Supabase via Session Pooler")
    p.add_argument("--año", choices=["2024", "2025"], default=None,
                   help="Procesar solo una convocatoria (omitir = ambas)")
    p.add_argument("--dry-run", action="store_true",
                   help="Parsea pero no guarda en BD")
    args = p.parse_args()

    if args.supabase:
        _load_supabase_secrets()
    else:
        os.environ.setdefault("DB_HOST",     "localhost")
        os.environ.setdefault("DB_PORT",     "5432")
        os.environ.setdefault("DB_NAME",     "stack_db")
        os.environ.setdefault("DB_USER",     "postgres")
        os.environ.setdefault("DB_PASSWORD", "postgres")

    convs = [args.año] if args.año else None
    run(convocatorias=convs, dry_run=args.dry_run)
