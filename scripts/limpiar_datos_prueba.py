"""
scripts/limpiar_datos_prueba.py

Borra TODO lo creado para validar el MVP con alumnos de prueba, dejando el
proyecto exactamente como estaba.

POR QUÉ EXISTE
--------------
Para probar el motor de aprendizaje hizo falta un banco mínimo, y eso obligó a
aprobar preguntas SIN revisión humana real. Eso **degrada la lógica de negocio**
(el banco revisado es el producto). Todo lo que se hizo así quedó marcado con
`preguntas_test.es_prueba = TRUE`, y los alumnos de prueba tienen emails
reconocibles. Este script revierte ambas cosas.

QUÉ HACE
--------
1. Preguntas con `es_prueba = TRUE`:
   - Las **generadas para la prueba** (fuente='ia' y sin revisar de verdad) se
     devuelven a "pendiente de revisión" (revisada=FALSE), para que pasen por el
     flujo real cuando toque. NO se borran: el trabajo de generación se conserva.
   - Se limpia su rastro de aprobación falsa (revisado_por / revisado_en).
2. Progreso de los alumnos de prueba: `progreso_usuario`, `plan_estudio`,
   `historial_simulacros`.
3. Simulacros de academia creados para la prueba.

QUÉ **NO** PUEDE HACER
----------------------
Borrar las cuentas de los alumnos de prueba de **Supabase Auth**: la app solo
tiene la clave `anon`, que no permite eliminar usuarios. Hay que borrarlas a mano
desde el dashboard de Supabase (Authentication → Users). El script te recuerda
cuáles son.

Uso:
  python3 scripts/limpiar_datos_prueba.py --supabase --dry-run   # ver qué haría
  python3 scripts/limpiar_datos_prueba.py --supabase             # hacerlo
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._supabase_env import load_supabase_secrets, use_local_defaults

# Los alumnos de prueba del MVP. Si añades más, ponlos aquí.
ALUMNOS_PRUEBA = [
    "alumno.mvp.uno@example.com",
    "alumno.mvp.dos@example.com",
]


def _uuids_de(cur, emails: list[str]) -> list[str]:
    """
    Resuelve email -> UUID de Supabase Auth.

    Importante: las tablas de progreso NO guardan el email, guardan el **UUID**
    del usuario (`alumno["user_id"]`). Además el tipo difiere entre tablas:
    `progreso_usuario`/`plan_estudio` lo guardan como TEXT y
    `historial_simulacros` como UUID — de ahí los casts explícitos de abajo.
    """
    cur.execute("SELECT id::text FROM auth.users WHERE email = ANY(%s)", (emails,))
    return [r[0] for r in cur.fetchall()]


def run(dry_run: bool = False) -> None:
    from app.db import get_connection

    marca = "[DRY-RUN] " if dry_run else ""
    print(f"{marca}Limpiando datos de prueba del MVP…\n")

    with get_connection() as conn:
        with conn.cursor() as cur:
            uuids = _uuids_de(cur, ALUMNOS_PRUEBA)
            print(f"  Alumnos de prueba encontrados en Supabase Auth: {len(uuids)}")
            for e in ALUMNOS_PRUEBA:
                print(f"    · {e}")
            print()
            # ── 1. Preguntas aprobadas sin revisión real ──────────────────────
            cur.execute("""
                SELECT COUNT(*) FILTER (WHERE revisada),
                       COUNT(*)
                FROM normas.preguntas_test WHERE es_prueba
            """)
            aprobadas, total = cur.fetchone()
            print(f"  Preguntas marcadas como prueba: {total}  ({aprobadas} aprobadas sin revisión real)")
            print("    -> vuelven a 'pendiente de revisión' (NO se borran: el trabajo se conserva)")
            if not dry_run:
                cur.execute("""
                    UPDATE normas.preguntas_test
                       SET revisada = FALSE, revisado_por = NULL, revisado_en = NULL,
                           es_prueba = FALSE
                     WHERE es_prueba
                """)
                print(f"    ✔ {cur.rowcount} revertidas")

            # ── 2. Progreso de los alumnos de prueba ──────────────────────────
            # user_id::text funciona igual si la columna es TEXT o UUID
            for tabla in ("respuestas", "progreso_usuario", "plan_estudio",
                          "historial_simulacros", "perfil_alumno"):
                cur.execute(
                    f"SELECT COUNT(*) FROM normas.{tabla} WHERE user_id::text = ANY(%s)",
                    (uuids,),
                )
                n = cur.fetchone()[0]
                print(f"  {tabla}: {n} filas de alumnos de prueba")
                if not dry_run and n:
                    cur.execute(
                        f"DELETE FROM normas.{tabla} WHERE user_id::text = ANY(%s)",
                        (uuids,),
                    )
                    print(f"    ✔ {cur.rowcount} borradas")

            # ── 3. Simulacros de academia de prueba ───────────────────────────
            cur.execute("""
                SELECT simulacro_id, nombre FROM normas.simulacros_academia
                WHERE nombre ILIKE '%%prueba%%' OR nombre ILIKE '%%mvp%%'
            """)
            sims = cur.fetchall()
            print(f"  Simulacros de academia de prueba: {len(sims)}")
            for sid, nombre in sims:
                print(f"    #{sid} — {nombre}")
            if not dry_run and sims:
                ids = [s[0] for s in sims]
                cur.execute("DELETE FROM normas.simulacro_academia_preguntas WHERE simulacro_id = ANY(%s)", (ids,))
                cur.execute("DELETE FROM normas.simulacros_academia WHERE simulacro_id = ANY(%s)", (ids,))
                print(f"    ✔ {len(ids)} borrados")

        if not dry_run:
            conn.commit()

    print("\n" + "=" * 66)
    if dry_run:
        print("DRY-RUN: no se ha tocado nada. Ejecuta sin --dry-run para limpiar.")
    else:
        print("Limpieza completada.")
    print("=" * 66)
    print("\n⚠️  PENDIENTE MANUAL — cuentas de Supabase Auth")
    print("   La clave `anon` no permite borrar usuarios. Elimina estas cuentas")
    print("   desde el dashboard (Authentication → Users):")
    for e in ALUMNOS_PRUEBA:
        print(f"     · {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--supabase", action="store_true", help="conectar a Supabase (vía Session Pooler)")
    ap.add_argument("--dry-run", action="store_true", help="mostrar qué se borraría, sin borrar")
    args = ap.parse_args()

    if args.supabase:
        load_supabase_secrets()
    else:
        use_local_defaults()

    run(dry_run=args.dry_run)
