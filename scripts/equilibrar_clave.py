"""
scripts/equilibrar_clave.py

Equilibra la posición de la respuesta correcta en las preguntas generadas por IA.

EL PROBLEMA (medido el 12/07/2026)
----------------------------------
El **86,4%** de las preguntas IA tenían la respuesta correcta en la opción "a"
(b: 6,8% · c: 5,7% · d: 1,1%). Es un sesgo del modelo al generar. El examen
oficial real está equilibrado (a: 27,8% · b: 22,5% · c: 31,6% · d: 18,2%).

POR QUÉ ES GRAVE (no es cosmético)
----------------------------------
1. El alumno aprende "ante la duda, marca la a", acierta **sin saber la ley**, y
   esa costumbre **le perjudica en el examen real**.
2. Corrompe **nuestras propias métricas**: dominio, dificultad empírica y el
   futuro "¿estoy listo?" estarían midiendo a alguien que adivina el patrón, no
   que aprende.

QUÉ HACE
--------
- Baraja las opciones **dirigiendo** la posición de la correcta para que el
  reparto final sea ~25% en cada letra (clave equilibrada, construcción de test
  estándar). No es un barajado aleatorio: el aleatorio deja la distribución
  desigual por azar.
- **Remapea las letras dentro de la explicación**: 59 de 88 explicaciones citan
  las opciones por letra ("La opción b) es incorrecta porque…"). Barajar sin
  remapear las dejaría **señalando a la opción equivocada**.
- **No toca las referencias a artículos** ("artículo 10.2.c)"): el patrón exige
  que la letra NO vaya precedida de dígito ni punto.
- **No toca las preguntas oficiales**: son el examen real, su reparto ya es
  auténtico y no se debe alterar.

Validación automática: tras el remapeo, ninguna explicación puede decir que la
opción correcta es "incorrecta". Si ocurre, aborta.

Uso:
  python3 scripts/equilibrar_clave.py --supabase --dry-run
  python3 scripts/equilibrar_clave.py --supabase
"""

import re
import sys
import random
import argparse
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._supabase_env import load_supabase_secrets, use_local_defaults

LETRAS = "abcd"

# Letra que se refiere a una OPCIÓN: precedida de espacio o inicio, nunca de un
# dígito ni un punto — así "artículo 10.2.c)" queda intacto.
_RE_OPCION = re.compile(r'(?<![\d.])\b([abcd])\)')


def _remap(texto: str | None, mapa: dict[str, str]) -> str | None:
    """Sustitución SIMULTÁNEA de letras (si fuera secuencial, a→b→c encadenaría mal)."""
    if not texto:
        return texto
    return _RE_OPCION.sub(lambda m: f"{mapa[m.group(1)]})", texto)


def run(dry_run: bool = False, semilla: int = 20260712) -> None:
    from app.db import get_connection

    random.seed(semilla)   # reproducible

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pregunta_id, pregunta, opcion_a, opcion_b, opcion_c, opcion_d,
                       correcta, explicacion
                FROM normas.preguntas_test
                WHERE fuente = 'ia' AND revisada AND activa AND NOT descartada
                ORDER BY pregunta_id
            """)
            filas = cur.fetchall()

            if not filas:
                print("No hay preguntas IA que equilibrar.")
                return

            antes = Counter(f[6] for f in filas)
            n = len(filas)

            # Clave equilibrada: se reparten las posiciones a partes iguales y se
            # barajan. Un barajado puramente aleatorio dejaría el reparto desigual.
            destinos = [LETRAS[i % 4] for i in range(n)]
            random.shuffle(destinos)

            despues = Counter()
            incoherencias = []
            cambios = []

            for (pid, preg, a, b, c, d, corr, expl), destino in zip(filas, destinos):
                ops = {"a": a, "b": b, "c": c, "d": d}

                libres = [L for L in LETRAS if L != destino]
                otras  = [L for L in LETRAS if L != corr]
                random.shuffle(libres)
                mapa = {corr: destino}
                mapa.update(dict(zip(otras, libres)))

                nuevas = {mapa[k]: v for k, v in ops.items()}
                nueva_expl = _remap(expl, mapa)
                nueva_preg = _remap(preg, mapa)

                # La explicación no puede decir que la correcta es incorrecta
                if nueva_expl and re.search(
                        rf'opci[óo]n(?:es)?\s+{destino}\)[^.]{{0,40}}incorrect',
                        nueva_expl, re.I):
                    incoherencias.append(pid)

                despues[destino] += 1
                cambios.append((pid, nueva_preg, nuevas, destino, nueva_expl))

            print(f"Preguntas IA a equilibrar: {n}\n")
            print("Posición de la respuesta correcta:")
            for L in LETRAS:
                print(f"   {L}: antes {antes[L]:>3} ({100*antes[L]/n:>5.1f}%)"
                      f"   ->   después {despues[L]:>3} ({100*despues[L]/n:>5.1f}%)")

            if incoherencias:
                print(f"\n❌ ABORTADO: {len(incoherencias)} explicaciones quedarían "
                      f"incoherentes: {incoherencias[:5]}")
                return
            print("\n✔ Validación: ninguna explicación señala como incorrecta la opción correcta.")

            if not dry_run:
                for pid, preg, nuevas, corr, expl in cambios:
                    cur.execute("""
                        UPDATE normas.preguntas_test
                           SET pregunta = %s,
                               opcion_a = %s, opcion_b = %s, opcion_c = %s, opcion_d = %s,
                               correcta = %s, explicacion = %s
                         WHERE pregunta_id = %s
                    """, (preg, nuevas["a"], nuevas["b"], nuevas["c"], nuevas["d"],
                          corr, expl, pid))

        if not dry_run:
            conn.commit()

    print("\n" + "=" * 62)
    print("DRY-RUN: no se ha escrito nada." if dry_run else "Clave equilibrada y guardada.")
    print("Las preguntas OFICIALES no se han tocado (son el examen real).")
    print("=" * 62)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--supabase", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.supabase:
        load_supabase_secrets()
    else:
        use_local_defaults()

    run(dry_run=args.dry_run)
