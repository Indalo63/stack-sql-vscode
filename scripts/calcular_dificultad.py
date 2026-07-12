"""
scripts/calcular_dificultad.py

Calcula la dificultad de las preguntas (migración 047). Dos mecanismos, y el
segundo manda sobre el primero:

1. HEURÍSTICA (provisional, sin IA y sin coste).
   Señales objetivas del texto, no opiniones:
     · ¿La pregunta exige un DATO EXACTO? (plazo, porcentaje, mayoría, cuantía).
       Recordar dígitos es más difícil que reconocer un concepto.
     · ¿Se parecen mucho los distractores entre sí? Si las cuatro opciones son
       casi iguales, hay que hilar fino: la pregunta es más difícil. Se mide con
       la similitud media entre pares de opciones, y se corta por TERCILES del
       propio banco (no por un umbral inventado).
     · ¿Es una pregunta conceptual ("qué se entiende por…")? Suele ser más fácil.

   ⚠️ Esto es una CONJETURA, no un dato. Queda marcada como tal
   (`dificultad_origen = 'heuristica'`) para que nadie la confunda con una medida.

2. EMPÍRICA (la buena).
   La dificultad de un ítem se DEFINE como el porcentaje de examinandos que lo
   acierta. En cuanto una pregunta acumula suficientes respuestas reales
   (`min_respuestas_dificultad`), se calcula de verdad y **sustituye** a la
   heurística. Cuantos más alumnos, más exacta.

Uso:
  python3 scripts/calcular_dificultad.py --supabase --dry-run   # ver, sin escribir
  python3 scripts/calcular_dificultad.py --supabase             # aplicar
  python3 scripts/calcular_dificultad.py --supabase --solo-empirica
"""

import re
import sys
import argparse
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._supabase_env import load_supabase_secrets, use_local_defaults

# La pregunta exige recordar un dato exacto -> más difícil
_DATO_EXACTO = re.compile(
    r"\b(plazo|d[íi]as?|meses|a[ñn]os?|por ciento|porcentaje|mayor[íi]a|qu[óo]rum|"
    r"n[úu]mero|cu[áa]nt[oa]s?|cuant[íi]a|tres quintos|dos tercios|mitad)\b", re.I)

# Pregunta conceptual -> suele ser más fácil (se reconoce, no se recuerda)
_CONCEPTUAL = re.compile(
    r"\b(concepto|definici[óo]n|qu[ée] se entiende|naturaleza|principios?|"
    r"caracter[íi]stic)\b", re.I)


def _similitud_distractores(opciones: list[str]) -> float:
    """Similitud media entre pares de opciones. Alta = hay que hilar fino."""
    pares = [(a, b) for i, a in enumerate(opciones) for b in opciones[i + 1:]]
    if not pares:
        return 0.0
    return sum(SequenceMatcher(None, a.lower(), b.lower()).ratio()
               for a, b in pares) / len(pares)


def _dificultad_heuristica(pregunta: str, opciones: list[str],
                           t1: float, t2: float) -> int:
    """1 fácil · 2 media · 3 difícil. t1/t2 = terciles de similitud del banco."""
    score = 0
    if _DATO_EXACTO.search(pregunta):
        score += 1
    if _CONCEPTUAL.search(pregunta):
        score -= 1
    sim = _similitud_distractores(opciones)
    if sim >= t2:
        score += 1
    elif sim <= t1:
        score -= 1
    return max(1, min(3, 2 + score))


def _dificultad_empirica(pct_acierto: float) -> int:
    """
    Índice de dificultad clásico: cuanto MÁS aciertan, más fácil.
    (Con 4 opciones, el azar da un 25%: por debajo de eso ya es casi ruido.)
    """
    if pct_acierto >= 70:
        return 1      # fácil
    if pct_acierto >= 40:
        return 2      # media
    return 3          # difícil


def run(dry_run: bool = False, solo_empirica: bool = False) -> None:
    from app.db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(MAX(min_respuestas_dificultad), 20)
                FROM normas.parametros_aprendizaje WHERE oposicion_id = 1
            """)
            min_resp = cur.fetchone()[0]

            # ── 1. EMPÍRICA: el dato real manda ──────────────────────────────
            cur.execute("""
                SELECT pt.pregunta_id,
                       SUM(pu.total_vistas)    AS respuestas,
                       SUM(pu.total_correctas) AS aciertos
                FROM normas.preguntas_test pt
                JOIN normas.progreso_usuario pu ON pu.pregunta_id = pt.pregunta_id
                WHERE pt.revisada AND pt.activa
                GROUP BY pt.pregunta_id
                HAVING SUM(pu.total_vistas) >= %s
            """, (min_resp,))
            empiricas = cur.fetchall()

            print(f"Umbral para fiarse del dato real: {min_resp} respuestas")
            print(f"Preguntas con datos suficientes: {len(empiricas)}")
            for pid, resp, aciertos in empiricas:
                pct = round(100 * aciertos / resp, 2)
                dif = _dificultad_empirica(pct)
                if not dry_run:
                    cur.execute("""
                        UPDATE normas.preguntas_test
                           SET dificultad = %s, dificultad_origen = 'empirica',
                               dificultad_n = %s, dificultad_pct = %s
                         WHERE pregunta_id = %s
                    """, (dif, resp, pct, pid))

            if solo_empirica:
                if not dry_run:
                    conn.commit()
                print("(--solo-empirica: no se toca la heurística)")
                return

            # ── 2. HEURÍSTICA: solo donde NO hay dato real ───────────────────
            cur.execute("""
                SELECT pregunta_id, pregunta, opcion_a, opcion_b, opcion_c, opcion_d
                FROM normas.preguntas_test
                WHERE revisada AND activa AND dificultad_origen <> 'empirica'
            """)
            filas = cur.fetchall()

            # Terciles del propio banco: no se inventa un umbral
            sims = sorted(_similitud_distractores([r[2], r[3], r[4], r[5]]) for r in filas)
            if not sims:
                print("No hay preguntas a las que aplicar la heurística.")
                return
            t1 = sims[len(sims) // 3]
            t2 = sims[2 * len(sims) // 3]
            print(f"\nTerciles de similitud entre distractores: {t1:.2f} / {t2:.2f}")

            reparto = {1: 0, 2: 0, 3: 0}
            for pid, preg, a, b, c, d in filas:
                dif = _dificultad_heuristica(preg, [a, b, c, d], t1, t2)
                reparto[dif] += 1
                if not dry_run:
                    cur.execute("""
                        UPDATE normas.preguntas_test
                           SET dificultad = %s, dificultad_origen = 'heuristica'
                         WHERE pregunta_id = %s
                    """, (dif, pid))

            print(f"Heurística aplicada a {len(filas)} preguntas (PROVISIONAL):")
            for k, etiqueta in ((1, "fácil"), (2, "media"), (3, "difícil")):
                print(f"   {k} ({etiqueta:<7}): {reparto[k]}")

        if not dry_run:
            conn.commit()

    print("\n" + "=" * 60)
    if dry_run:
        print("DRY-RUN: no se ha escrito nada.")
    else:
        print("Hecho.")
    print("La heurística es una CONJETURA (dificultad_origen='heuristica').")
    print("El acierto real de los alumnos la sustituirá en cuanto haya datos.")
    print("=" * 60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--supabase", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--solo-empirica", action="store_true",
                    help="recalcular solo con datos reales (para ejecutar periódicamente)")
    args = ap.parse_args()

    if args.supabase:
        load_supabase_secrets()
    else:
        use_local_defaults()

    run(dry_run=args.dry_run, solo_empirica=args.solo_empirica)
