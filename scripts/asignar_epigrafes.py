"""
scripts/asignar_epigrafes.py

Clasifica preguntas de normas.preguntas_test contra el temario oficial
(normas.epigrafes) usando Claude: dado el texto de la pregunta y el bloque
de su ley, determina a qué tema del programa pertenece.

Reutilizable para cualquier oposición (parámetro --oposicion, sin fijar
código por defecto en las queries) y para re-sincronizar el banco si el
temario oficial cambia de estructura en el futuro.

Uso:
  # Probar con pocas preguntas antes de lanzar el resto (revisión humana)
  python3 scripts/asignar_epigrafes.py --supabase --limit 5 --dry-run

  # Backfill completo
  python3 scripts/asignar_epigrafes.py --supabase --n 300
"""

import os
import re
import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._supabase_env import load_supabase_secrets as _load_supabase_secrets


def _fetch_pendientes(limit=None, pregunta_id=None):
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            sql = """
                SELECT p.pregunta_id, p.ley_id, p.articulo, p.pregunta,
                       p.opcion_a, p.opcion_b, p.opcion_c, p.opcion_d, l.nombre,
                       t.denominacion AS titulo_nombre
                FROM normas.preguntas_test p
                JOIN normas.leyes l ON l.ley_id = p.ley_id
                LEFT JOIN normas.articulos a
                  ON a.ley_id = p.ley_id
                 AND a.numero = split_part(p.articulo, '.', 1)
                 AND a.tipo = 'articulo'
                LEFT JOIN normas.titulos t ON t.titulo_id = a.titulo_id
                WHERE p.epigrafe_id IS NULL
            """
            params = []
            if pregunta_id:
                sql += " AND p.pregunta_id = %s"
                params.append(pregunta_id)
            sql += " ORDER BY p.pregunta_id"
            if limit:
                sql += " LIMIT %s"
                params.append(limit)
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _actualizar_epigrafe(pregunta_id, epigrafe_id):
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE normas.preguntas_test SET epigrafe_id = %s WHERE pregunta_id = %s",
                (epigrafe_id, pregunta_id),
            )
        conn.commit()


def _build_prompt(pregunta, epigrafes):
    temas_txt = "\n".join(f"{e['tema']}. {e['titulo']}" for e in epigrafes)
    opts = "\n".join(f"{k}) {pregunta[f'opcion_{k}']}" for k in ("a", "b", "c", "d"))
    titulo_ctx = (
        f"El artículo pertenece al Título \"{pregunta['titulo_nombre']}\" de {pregunta['nombre']}.\n"
        if pregunta.get("titulo_nombre") else ""
    )
    return [{
        "role": "user",
        "content": (
            "Eres un experto en el temario de esta oposición. Dada la siguiente "
            "pregunta de examen, determina a qué tema del programa pertenece.\n\n"
            f"{titulo_ctx}"
            f"TEMAS DEL BLOQUE:\n{temas_txt}\n\n"
            f"PREGUNTA (artículo {pregunta['articulo']} de {pregunta['nombre']}):\n"
            f"{pregunta['pregunta']}\n{opts}\n\n"
            "Responde SOLO con el número de tema, sin texto adicional."
        ),
    }]


def _parse_tema(raw, temas_validos):
    m = re.search(r'\d+', raw)
    if not m:
        raise ValueError(f"No se encontró un número de tema en la respuesta: {raw!r}")
    tema = int(m.group())
    if tema not in temas_validos:
        raise ValueError(f"Tema {tema} no está entre los válidos {sorted(temas_validos)}")
    return tema


def run(oposicion="GACE", n=300, limit=None, pregunta_id=None, dry_run=False, delay=0.3):
    import anthropic
    from app.config import CLAUDE_MODEL, ANTHROPIC_API_KEY
    from app.retrieval import get_bloque_y_epigrafes

    preguntas = _fetch_pendientes(limit=limit or n, pregunta_id=pregunta_id)
    if not preguntas:
        print("No hay preguntas pendientes de clasificar (epigrafe_id IS NULL).")
        return

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    cache_epigrafes = {}
    ok = err = sin_bloque = 0

    for i, p in enumerate(preguntas, 1):
        ley_id = p["ley_id"]
        if ley_id not in cache_epigrafes:
            cache_epigrafes[ley_id] = get_bloque_y_epigrafes(ley_id, oposicion_codigo=oposicion)
        bloque, epigrafes = cache_epigrafes[ley_id]

        if not epigrafes:
            sin_bloque += 1
            print(f"  [SKIP] [{i:>3}/{len(preguntas)}] pregunta_id={p['pregunta_id']} "
                  f"— ley_id={ley_id} sin bloque/epígrafes en oposición {oposicion}")
            continue

        try:
            resp = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=20,
                messages=_build_prompt(p, epigrafes),
            )
            temas_validos = {e["tema"] for e in epigrafes}
            tema = _parse_tema(resp.content[0].text, temas_validos)
            epigrafe_id = next(e["epigrafe_id"] for e in epigrafes if e["tema"] == tema)
            titulo = next(e["titulo"] for e in epigrafes if e["tema"] == tema)

            if not dry_run:
                _actualizar_epigrafe(p["pregunta_id"], epigrafe_id)

            ok += 1
            tag = "[DRY]" if dry_run else "[OK] "
            print(f"  {tag} [{i:>3}/{len(preguntas)}] pregunta_id={p['pregunta_id']} "
                  f"(art. {p['articulo']} de {p['nombre']}) -> {bloque}.{tema} {titulo[:60]}")
        except Exception as e:
            err += 1
            print(f"  [ERR] [{i:>3}/{len(preguntas)}] pregunta_id={p['pregunta_id']} — {e}")

        if delay > 0 and i < len(preguntas):
            time.sleep(delay)

    print(f"\n{'=' * 60}")
    modo = "DRY-RUN, nada guardado" if dry_run else "guardado en normas.preguntas_test"
    print(f"TOTAL ({modo}): {ok} OK, {err} errores, {sin_bloque} sin bloque/epígrafes")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Clasifica preguntas contra el temario oficial (epígrafes)")
    p.add_argument("--supabase", action="store_true", help="Conectar a Supabase via Session Pooler")
    p.add_argument("--oposicion", default="GACE", help="Código de la oposición (default: GACE)")
    p.add_argument("--n", type=int, default=300, help="Máximo de preguntas a procesar (default: 300)")
    p.add_argument("--limit", type=int, default=None, help="Límite explícito (para pruebas con pocos ejemplos)")
    p.add_argument("--pregunta-id", type=int, default=None, help="Clasificar solo una pregunta concreta")
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

    run(oposicion=args.oposicion, n=args.n, limit=args.limit,
        pregunta_id=args.pregunta_id, dry_run=args.dry_run, delay=args.delay)
