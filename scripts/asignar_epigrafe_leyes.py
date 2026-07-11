"""
scripts/asignar_epigrafe_leyes.py

Clasifica los temas oficiales (normas.epigrafes) contra el catálogo de leyes
cargadas usando Claude: dado el título completo de un tema, determina qué
leyes de su mismo bloque son relevantes para ese tema. Puebla
normas.epigrafe_leyes (relación muchos-a-muchos), usada por el sidebar de
Administración para filtrar "Ley" una vez elegido un "Tema".

Reutilizable para cualquier oposición (parámetro --oposicion) y para
re-sincronizar la relación si el temario o el catálogo de leyes cambian: cada
ejecución reemplaza por completo las filas del tema procesado (DELETE +
INSERT), así que es seguro repetirla.

Uso:
  # Probar con un solo tema antes de lanzar el resto (revisión humana)
  python3 scripts/asignar_epigrafe_leyes.py --supabase --epigrafe-id 1 --dry-run

  # Backfill completo de una oposición
  python3 scripts/asignar_epigrafe_leyes.py --supabase --dry-run
  python3 scripts/asignar_epigrafe_leyes.py --supabase
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


def _fetch_temas(oposicion, epigrafe_id=None):
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            sql = """
                SELECT e.epigrafe_id, e.bloque, e.tema, e.titulo
                FROM normas.epigrafes e
                JOIN normas.oposiciones o ON o.oposicion_id = e.oposicion_id
                WHERE o.codigo = %s
            """
            params = [oposicion]
            if epigrafe_id:
                sql += " AND e.epigrafe_id = %s"
                params.append(epigrafe_id)
            sql += " ORDER BY e.orden"
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetch_leyes_oposicion(oposicion):
    """
    Catálogo completo de leyes candidatas para TODOS los temas (no solo las
    de su propio bloque): el bloque de una ley en oposicion_leyes es una
    clasificación administrativa del programa, no implica que esa ley sea
    irrelevante para un tema archivado en otro bloque (p. ej. LRJSP está en
    el bloque IV pero es la ley correcta para el tema I.9 "sector público
    institucional"; CE1978 está en el bloque I pero es la ley correcta para
    IV.2 "tipos de leyes, reserva de ley").
    """
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT l.ley_id, l.codigo, COALESCE(l.nombre_corto, l.nombre) AS nombre
                FROM normas.leyes l
                JOIN normas.oposicion_leyes ol ON ol.ley_id = l.ley_id
                JOIN normas.oposiciones o      ON o.oposicion_id = ol.oposicion_id
                WHERE o.codigo = %s
                  AND l.activa = TRUE AND ol.excluir_test = FALSE
                ORDER BY l.codigo
            """, (oposicion,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _reemplazar_epigrafe_leyes(epigrafe_id, ley_ids):
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM normas.epigrafe_leyes WHERE epigrafe_id = %s", (epigrafe_id,))
            if ley_ids:
                cur.executemany(
                    "INSERT INTO normas.epigrafe_leyes (epigrafe_id, ley_id) VALUES (%s, %s)",
                    [(epigrafe_id, lid) for lid in ley_ids],
                )
        conn.commit()


def _build_prompt(tema, leyes):
    catalogo = "\n".join(f"{l['codigo']}: {l['nombre']}" for l in leyes)
    return [{
        "role": "user",
        "content": (
            "Eres un experto en el temario de esta oposición. Dado el título "
            "completo de un tema del programa oficial, determina qué leyes del "
            "siguiente catálogo son relevantes para preparar ese tema. Un tema "
            "puede tocar varias leyes, una sola, o ninguna.\n\n"
            f"TEMA: {tema['bloque']}.{tema['tema']} — {tema['titulo']}\n\n"
            f"CATÁLOGO DE LEYES (código: nombre):\n{catalogo}\n\n"
            "Responde SOLO con los códigos de las leyes relevantes separados "
            "por comas (por ejemplo: LPAC,LRJSP), o NINGUNA si no aplica "
            "ninguna. Sin texto adicional."
        ),
    }]


def _parse_codigos(raw, codigos_validos):
    raw = raw.strip()
    if raw.upper().startswith("NINGUNA"):
        return set()
    encontrados = {c.strip().upper() for c in re.split(r"[,\s]+", raw) if c.strip()}
    return encontrados & {c.upper() for c in codigos_validos}


def run(oposicion="GACE", epigrafe_id=None, dry_run=False, delay=0.3):
    import anthropic
    from app.config import CLAUDE_MODEL, ANTHROPIC_API_KEY

    temas = _fetch_temas(oposicion, epigrafe_id=epigrafe_id)
    if not temas:
        print("No hay temas que procesar.")
        return

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    leyes = _fetch_leyes_oposicion(oposicion)
    ok = err = sin_leyes_bloque = 0

    if not leyes:
        print(f"No hay leyes cargadas para la oposición {oposicion}.")
        return

    for i, t in enumerate(temas, 1):
        bloque = t["bloque"]

        try:
            resp = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=200,
                messages=_build_prompt(t, leyes),
            )
            codigos_validos = {l["codigo"] for l in leyes}
            codigos_elegidos = _parse_codigos(resp.content[0].text, codigos_validos)
            ley_ids = [l["ley_id"] for l in leyes if l["codigo"].upper() in codigos_elegidos]

            if not dry_run:
                _reemplazar_epigrafe_leyes(t["epigrafe_id"], ley_ids)

            ok += 1
            tag = "[DRY]" if dry_run else "[OK] "
            etiqueta_leyes = ", ".join(sorted(codigos_elegidos)) or "(ninguna)"
            print(f"  {tag} [{i:>2}/{len(temas)}] {bloque}.{t['tema']} "
                  f"{t['titulo'][:55]}… -> {etiqueta_leyes}")
        except Exception as e:
            err += 1
            print(f"  [ERR] [{i:>2}/{len(temas)}] {bloque}.{t['tema']} — {e}")

        if delay > 0 and i < len(temas):
            time.sleep(delay)

    print(f"\n{'=' * 60}")
    modo = "DRY-RUN, nada guardado" if dry_run else "guardado en normas.epigrafe_leyes"
    print(f"TOTAL ({modo}): {ok} OK, {err} errores, {sin_leyes_bloque} sin leyes en el bloque")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Clasifica temas del programa contra el catálogo de leyes")
    p.add_argument("--supabase", action="store_true", help="Conectar a Supabase via Session Pooler")
    p.add_argument("--oposicion", default="GACE", help="Código de la oposición (default: GACE)")
    p.add_argument("--epigrafe-id", type=int, default=None, help="Clasificar solo un tema concreto")
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

    run(oposicion=args.oposicion, epigrafe_id=args.epigrafe_id,
        dry_run=args.dry_run, delay=args.delay)
