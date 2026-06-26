"""
scripts/build_test_bank.py

Genera preguntas tipo test en lote y las guarda en normas.preguntas_test.
Las preguntas se guardan con revisada=FALSE hasta que el formador las apruebe.

Uso:
  # Contra el Docker local (usa credenciales de .env)
  python scripts/build_test_bank.py --ley-id 1 --n 5 --dry-run   # prueba CE
  python scripts/build_test_bank.py --ley-id 1 --n 50             # genera 50 preguntas CE

  # Contra Supabase (usa credenciales de .streamlit/secrets.toml)
  python scripts/build_test_bank.py --supabase --ley-id 1 --n 50
  python scripts/build_test_bank.py --supabase --n 50             # todas las leyes

Coste estimado: ~0,01 € por pregunta (Claude Sonnet 4.6)
  50 preguntas × 6 leyes = 300 preguntas ≈ 3 €
"""

import os
import re
import sys
import json
import time
import argparse
from pathlib import Path


def _load_supabase_secrets():
    """Carga .streamlit/secrets.toml en os.environ para conectar a Supabase."""
    secrets_path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print("ERROR: .streamlit/secrets.toml no encontrado.", file=sys.stderr)
        sys.exit(1)
    for line in secrets_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip().strip('"').strip("'")
    print("Credenciales cargadas desde .streamlit/secrets.toml (Supabase)")


import anthropic
from app.config import CLAUDE_MODEL, ANTHROPIC_API_KEY
from app.db import get_connection

MIN_LENGTH = 200


# ── Consultas BD ──────────────────────────────────────────────────────────────

def _get_leyes(ley_id=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            sql = "SELECT ley_id, nombre FROM normas.leyes WHERE activa = TRUE"
            params = ()
            if ley_id:
                sql += " AND ley_id = %s"
                params = (ley_id,)
            cur.execute(sql + " ORDER BY ley_id", params)
            return [{"ley_id": r[0], "nombre": r[1]} for r in cur.fetchall()]


def _fetch_articles(ley_id, n):
    """Artículos no generados aún, ponderados por longitud de contenido."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.numero, a.titulo_id, a.contenido
                FROM normas.articulos a
                WHERE a.ley_id = %s
                  AND a.tipo = 'articulo'
                  AND length(a.contenido) >= %s
                  AND a.contenido !~* '\\(derogado|sin contenido|suprimido\\)'
                  AND NOT EXISTS (
                      SELECT 1 FROM normas.preguntas_test p
                      WHERE p.ley_id = a.ley_id AND p.articulo = a.numero
                  )
                ORDER BY RANDOM() * log(length(a.contenido)) DESC
                LIMIT %s
            """, (ley_id, MIN_LENGTH, n))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _save(ley_id, art, parsed):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO normas.preguntas_test
                    (ley_id, titulo_id, articulo, pregunta,
                     opcion_a, opcion_b, opcion_c, opcion_d, correcta, explicacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ley_id,
                art.get("titulo_id"),
                art["numero"],
                parsed["pregunta"],
                parsed["opciones"]["a"],
                parsed["opciones"]["b"],
                parsed["opciones"]["c"],
                parsed["opciones"]["d"],
                parsed["correcta"],
                parsed.get("explicacion", ""),
            ))
        conn.commit()


# ── Generación ────────────────────────────────────────────────────────────────

def _build_prompt(art, ley_nombre):
    return [{
        "role": "user",
        "content": (
            f"Eres un experto en Derecho español y creador de exámenes de oposición al "
            f"Cuerpo de Gestión de la Administración Civil del Estado (GACE).\n\n"
            f"A partir del siguiente artículo de {ley_nombre}, genera UNA pregunta tipo "
            f"test con exactamente 4 opciones (a, b, c, d), siguiendo el estilo oficial "
            f"del examen GACE.\n\n"
            f"REGLAS DE ESTILO OBLIGATORIAS:\n"
            f"1. El enunciado DEBE comenzar con 'Según el artículo [número] de {ley_nombre},' "
            f"o 'De acuerdo con el artículo [número] de {ley_nombre},'\n"
            f"2. Opciones en a), b), c), d) minúsculas.\n"
            f"3. Distractores con error sutil y técnico: plazo distinto, porcentaje diferente, "
            f"órgano incorrecto o palabra clave cambiada. Nunca distractores conceptualmente "
            f"muy distintos.\n"
            f"4. Nivel alto: datos exactos (plazos, porcentajes, órganos, requisitos), no "
            f"conceptos generales.\n"
            f"5. Sin símbolos matemáticos. En texto: 'igual a', 'mayor que', 'porcentaje', etc.\n\n"
            f"ARTÍCULO {art['numero']}:\n{art['contenido']}\n\n"
            f"Responde SOLO con JSON válido, sin texto adicional:\n"
            f'{{"articulo":"{art["numero"]}","pregunta":"...","opciones":{{"a":"...","b":"...","c":"...","d":"..."}},"correcta":"a","explicacion":"..."}}'
        ),
    }]


def _parse_and_validate(raw):
    """Extrae el JSON de la respuesta y normaliza claves."""
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if not m:
        raise ValueError("No se encontró JSON en la respuesta")
    parsed = json.loads(m.group())

    # Normalizar 'correcta': "a)" → "a", "A" → "a"
    c = parsed.get("correcta", "").strip().lower().replace(")", "").replace(".", "")[:1]
    if c not in "abcd":
        raise ValueError(f"Valor de 'correcta' inválido: {parsed.get('correcta')!r}")
    parsed["correcta"] = c

    # Normalizar claves de opciones: "a)" → "a"
    raw_opts = parsed.get("opciones", {})
    opts = {k.strip().lower().replace(")", "")[:1]: v for k, v in raw_opts.items()}
    if not all(k in opts for k in "abcd"):
        raise ValueError(f"Opciones incompletas: {list(opts.keys())}")
    parsed["opciones"] = opts

    if not parsed.get("pregunta"):
        raise ValueError("Campo 'pregunta' vacío")

    return parsed


# ── Runner principal ──────────────────────────────────────────────────────────

def run(ley_id=None, n=50, dry_run=False, delay=0.5):
    leyes = _get_leyes(ley_id)
    if not leyes:
        print("No se encontraron leyes activas.")
        return

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    total_ok = total_err = 0

    for ley in leyes:
        print(f"\n{'─' * 60}")
        print(f"Ley: {ley['nombre']}  (id={ley['ley_id']})")
        arts = _fetch_articles(ley["ley_id"], n)
        if not arts:
            print("  Sin artículos nuevos que procesar.")
            continue
        print(f"  Artículos a generar: {len(arts)}")

        ok = err = 0
        for i, art in enumerate(arts, 1):
            try:
                resp = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=650,
                    messages=_build_prompt(art, ley["nombre"]),
                )
                parsed = _parse_and_validate(resp.content[0].text)

                if not dry_run:
                    _save(ley["ley_id"], art, parsed)

                ok += 1
                tag = "[DRY]" if dry_run else "[OK] "
                print(f"  {tag} [{i:>3}/{len(arts)}] Art. {art['numero']}")
            except Exception as e:
                err += 1
                print(f"  [ERR] [{i:>3}/{len(arts)}] Art. {art['numero']} — {e}")

            if delay > 0 and i < len(arts):
                time.sleep(delay)

        print(f"  Resultado: {ok} generadas, {err} errores")
        total_ok += ok
        total_err += err

    print(f"\n{'=' * 60}")
    if dry_run:
        print(f"TOTAL (dry-run, nada guardado): {total_ok} OK, {total_err} errores")
    else:
        print(f"TOTAL guardadas en normas.preguntas_test: {total_ok} OK, {total_err} errores")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Genera banco de preguntas GACE")
    p.add_argument("--supabase", action="store_true",
                   help="Conectar a Supabase (lee .streamlit/secrets.toml)")
    p.add_argument("--ley-id", type=int, default=None,
                   help="ID de la ley a procesar (omitir = todas las activas)")
    p.add_argument("--n", type=int, default=50,
                   help="Número de preguntas por ley (default: 50)")
    p.add_argument("--dry-run", action="store_true",
                   help="Genera preguntas pero NO las guarda en BD")
    p.add_argument("--delay", type=float, default=0.5,
                   help="Segundos entre llamadas a la API (default: 0.5)")
    args = p.parse_args()

    if args.supabase:
        _load_supabase_secrets()

    run(ley_id=args.ley_id, n=args.n, dry_run=args.dry_run, delay=args.delay)
