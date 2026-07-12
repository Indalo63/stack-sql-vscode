"""
scripts/calcular_confundibles.py

Calcula qué pares de leyes son CONFUNDIBLES y los guarda en
`normas.pares_confundibles` (migración 051). Alimenta la práctica intercalada.

DE DÓNDE SALEN (no se inventan)
-------------------------------
Dos leyes se confunden si el **programa oficial las estudia juntas**. Ese dato ya
lo tenemos: `normas.epigrafe_leyes` dice qué leyes toca cada tema. El solapamiento
de temas entre dos leyes es la medida.

POR QUÉ JACCARD Y NO EL CONTEO BRUTO
------------------------------------
El conteo bruto premia a las leyes **ubicuas**. La CE1978 aparece en 28 temas y la
LRJSP en 24: comparten muchos temas con TODAS las demás, y no por eso se confunden
con todas. Jaccard normaliza:

    fuerza = compartidos / (temas_A + temas_B − compartidos)

Resultado sobre GACE: salen exactamente los pares que un opositor reconocería
—LPAC/LRJSP, ley y su reglamento (LEF/RLEF, LGS/RLGS), TUE/TFUE, TREBEP/LMRFP—
y NO sale "CE1978 con todo".

RE-EJECUTABLE
-------------
Borra e inserta los pares de la oposición (no acumula). Si el temario cambia o se
carga una ley nueva, se vuelve a lanzar y ya está.

Uso:
  python3 scripts/calcular_confundibles.py --supabase --dry-run
  python3 scripts/calcular_confundibles.py --supabase
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._supabase_env import load_supabase_secrets, use_local_defaults

# Por debajo de esto, el solapamiento es anecdótico: dos leyes que coinciden en un
# tema suelto no son "confundibles", solo vecinas. Intercalarlas no entrena nada.
_FUERZA_MINIMA = 0.20

# Un par sin preguntas suficientes en el banco no se puede intercalar (haría falta
# alternar y no habría con qué). Se descarta al calcular, no en la UI.
_MIN_PREGUNTAS_POR_LEY = 3


def run(oposicion_id: int = 1, dry_run: bool = False) -> None:
    from app.db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                WITH temas AS (
                    SELECT el.ley_id,
                           array_agg(el.epigrafe_id) AS ts,
                           COUNT(*)                  AS n
                    FROM normas.epigrafe_leyes el
                    JOIN normas.oposicion_leyes ol ON ol.ley_id = el.ley_id
                                                  AND ol.oposicion_id = %s
                                                  AND NOT ol.excluir_test
                    GROUP BY el.ley_id
                ),
                banco AS (
                    SELECT ley_id, COUNT(*) AS n_preg
                    FROM normas.preguntas_test
                    WHERE revisada AND activa AND NOT descartada
                    GROUP BY ley_id
                ),
                pares AS (
                    SELECT a.ley_id AS ley_a, b.ley_id AS ley_b,
                           cardinality(ARRAY(
                               SELECT unnest(a.ts) INTERSECT SELECT unnest(b.ts)
                           )) AS comp,
                           a.n AS na, b.n AS nb
                    FROM temas a
                    JOIN temas b ON a.ley_id < b.ley_id
                    JOIN banco  ba ON ba.ley_id = a.ley_id AND ba.n_preg >= %s
                    JOIN banco  bb ON bb.ley_id = b.ley_id AND bb.n_preg >= %s
                )
                SELECT p.ley_a, p.ley_b, p.comp,
                       ROUND(p.comp::numeric / (p.na + p.nb - p.comp), 3) AS fuerza,
                       la.codigo, lb.codigo
                FROM pares p
                JOIN normas.leyes la ON la.ley_id = p.ley_a
                JOIN normas.leyes lb ON lb.ley_id = p.ley_b
                WHERE p.comp > 0
                  AND p.comp::numeric / (p.na + p.nb - p.comp) >= %s
                ORDER BY fuerza DESC, p.comp DESC
            """, (oposicion_id, _MIN_PREGUNTAS_POR_LEY, _MIN_PREGUNTAS_POR_LEY, _FUERZA_MINIMA))
            filas = cur.fetchall()

            print(f"Pares confundibles detectados: {len(filas)}")
            print(f"(fuerza >= {_FUERZA_MINIMA}, y al menos "
                  f"{_MIN_PREGUNTAS_POR_LEY} preguntas en banco de cada ley)\n")
            for ley_a, ley_b, comp, fuerza, cod_a, cod_b in filas:
                print(f"  {cod_a:10} + {cod_b:10}  {comp:2} temas en común   fuerza {fuerza}")

            if not filas:
                print("\nNinguno. Con el banco actual no hay pares intercalables:")
                print("hacen falta preguntas revisadas de AMBAS leyes del par.")
                return

            if dry_run:
                print("\nDRY-RUN: no se ha escrito nada.")
                return

            cur.execute("DELETE FROM normas.pares_confundibles WHERE oposicion_id = %s",
                        (oposicion_id,))
            for ley_a, ley_b, comp, fuerza, _ca, _cb in filas:
                cur.execute("""
                    INSERT INTO normas.pares_confundibles
                        (oposicion_id, ley_a, ley_b, temas_compartidos, fuerza, origen)
                    VALUES (%s, %s, %s, %s, %s, 'programa')
                """, (oposicion_id, ley_a, ley_b, comp, fuerza))
        conn.commit()

    print(f"\nGuardados {len(filas)} pares en normas.pares_confundibles.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--supabase", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--oposicion-id", type=int, default=1)
    args = ap.parse_args()

    if args.supabase:
        load_supabase_secrets()
    else:
        use_local_defaults()

    run(oposicion_id=args.oposicion_id, dry_run=args.dry_run)
