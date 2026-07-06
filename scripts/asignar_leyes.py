"""
scripts/asignar_leyes.py

Resuelve el ley_id de preguntas oficiales (normas.preguntas_test) que lo tienen
a NULL. El texto de estas preguntas cita el nombre completo de la norma
(regla obligatoria de estilo GACE), así que se puede identificar la ley
comparando contra el catálogo de leyes ya cargadas — sin forzar una
coincidencia si la norma no está en el catálogo (preguntas de actualidad o
de normas aún no cargadas se quedan correctamente en NULL).

Uso:
  python3 scripts/asignar_leyes.py --supabase --limit 10 --dry-run
  python3 scripts/asignar_leyes.py --supabase --n 200
"""

import os
import re
import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


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


def _fetch_pendientes(limit=None, pregunta_id=None):
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            sql = """
                SELECT pregunta_id, pregunta
                FROM normas.preguntas_test
                WHERE ley_id IS NULL
            """
            params = []
            if pregunta_id:
                sql += " AND pregunta_id = %s"
                params.append(pregunta_id)
            sql += " ORDER BY pregunta_id"
            if limit:
                sql += " LIMIT %s"
                params.append(limit)
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetch_catalogo_leyes():
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ley_id, codigo, nombre, numero_oficial
                FROM normas.leyes
                WHERE activa = TRUE
                ORDER BY ley_id
            """)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _actualizar_ley(pregunta_id, ley_id):
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE normas.preguntas_test SET ley_id = %s WHERE pregunta_id = %s",
                (ley_id, pregunta_id),
            )
        conn.commit()


def _build_prompt(pregunta_texto, catalogo):
    catalogo_txt = "\n".join(
        f"{l['ley_id']}: {l['nombre']}" + (f" ({l['numero_oficial']})" if l['numero_oficial'] else "")
        for l in catalogo
    )
    return [{
        "role": "user",
        "content": (
            "Dada la siguiente pregunta de examen, identifica a qué norma del "
            "catálogo se refiere (la pregunta cita el nombre completo de la norma "
            "en su enunciado).\n\n"
            f"CATÁLOGO DE NORMAS (id: nombre):\n{catalogo_txt}\n\n"
            f"PREGUNTA:\n{pregunta_texto}\n\n"
            "Responde SOLO con el id numérico de la norma si está en el catálogo, "
            "o la palabra NINGUNA si la norma citada no aparece en el catálogo. "
            "Sin texto adicional."
        ),
    }]


def _parse_respuesta(raw, ids_validos):
    raw = raw.strip().upper()
    if "NINGUNA" in raw:
        return None
    m = re.search(r'\d+', raw)
    if not m:
        raise ValueError(f"Respuesta no reconocida: {raw!r}")
    ley_id = int(m.group())
    if ley_id not in ids_validos:
        raise ValueError(f"ley_id {ley_id} no está en el catálogo")
    return ley_id


def run(n=200, limit=None, pregunta_id=None, dry_run=False, delay=0.3):
    import anthropic
    from app.config import CLAUDE_MODEL, ANTHROPIC_API_KEY

    preguntas = _fetch_pendientes(limit=limit or n, pregunta_id=pregunta_id)
    if not preguntas:
        print("No hay preguntas pendientes de resolver ley_id.")
        return

    catalogo = _fetch_catalogo_leyes()
    ids_validos = {l["ley_id"] for l in catalogo}
    print(f"Catálogo: {len(catalogo)} leyes activas.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    ok = ninguna = err = 0

    for i, p in enumerate(preguntas, 1):
        try:
            resp = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=20,
                messages=_build_prompt(p["pregunta"], catalogo),
            )
            ley_id = _parse_respuesta(resp.content[0].text, ids_validos)

            if ley_id is None:
                ninguna += 1
                print(f"  [----] [{i:>3}/{len(preguntas)}] pregunta_id={p['pregunta_id']} "
                      f"— ninguna norma del catálogo coincide")
                continue

            if not dry_run:
                _actualizar_ley(p["pregunta_id"], ley_id)

            ok += 1
            nombre = next(l["nombre"] for l in catalogo if l["ley_id"] == ley_id)
            tag = "[DRY]" if dry_run else "[OK] "
            print(f"  {tag} [{i:>3}/{len(preguntas)}] pregunta_id={p['pregunta_id']} "
                  f"-> ley_id={ley_id} ({nombre[:60]})")
        except Exception as e:
            err += 1
            print(f"  [ERR] [{i:>3}/{len(preguntas)}] pregunta_id={p['pregunta_id']} — {e}")

        if delay > 0 and i < len(preguntas):
            time.sleep(delay)

    print(f"\n{'=' * 60}")
    modo = "DRY-RUN, nada guardado" if dry_run else "guardado en normas.preguntas_test"
    print(f"TOTAL ({modo}): {ok} resueltas, {ninguna} sin coincidencia, {err} errores")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Resuelve ley_id de preguntas oficiales sin mapear")
    p.add_argument("--supabase", action="store_true", help="Conectar a Supabase via Session Pooler")
    p.add_argument("--n", type=int, default=200, help="Máximo de preguntas a procesar (default: 200)")
    p.add_argument("--limit", type=int, default=None, help="Límite explícito (para pruebas)")
    p.add_argument("--pregunta-id", type=int, default=None, help="Resolver solo una pregunta concreta")
    p.add_argument("--dry-run", action="store_true", help="Clasifica pero NO guarda en BD")
    p.add_argument("--delay", type=float, default=0.3, help="Segundos entre llamadas a la API")
    args = p.parse_args()

    if args.supabase:
        _load_supabase_secrets()
    else:
        os.environ.setdefault("DB_HOST", "localhost")
        os.environ.setdefault("DB_PORT", "5432")
        os.environ.setdefault("DB_NAME", "stack_db")
        os.environ.setdefault("DB_USER", "postgres")
        os.environ.setdefault("DB_PASSWORD", "postgres")

    run(n=args.n, limit=args.limit, pregunta_id=args.pregunta_id,
        dry_run=args.dry_run, delay=args.delay)
