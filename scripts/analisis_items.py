"""
scripts/analisis_items.py

Análisis psicométrico del banco: detecta preguntas DEFECTUOSAS de forma
automática (migración 049).

QUÉ DETECTA
-----------
1. `clave_sospechosa` — **la más grave**. Dos síntomas, misma causa probable:
     · Discriminación NEGATIVA: los alumnos que dominan la materia fallan esta
       pregunta MÁS que los que no la dominan. Eso no pasa por azar.
     · Un distractor se elige MÁS que la respuesta correcta.
   En ambos casos, lo más probable es que **la respuesta esté mal marcada**, o
   que la pregunta sea ambigua y el distractor sea defendible.
   Ningún editor puede revisar 1.800 preguntas a mano buscando esto. Esto las
   señala solo.

2. `no_discrimina` — la aciertan (o fallan) todos por igual. No mide nada: no
   distingue al que sabe del que no. Ocupa sitio sin aportar.

3. `distractor_muerto` — alguna opción incorrecta no la elige NADIE. La pregunta
   es de 3 opciones en la práctica: es más fácil de lo que parece, y su
   dificultad está mal estimada.

CÓMO SE CALCULA LA DISCRIMINACIÓN
---------------------------------
Correlación biserial-puntual entre acertar el ítem (1/0) y la **capacidad
general** del alumno. La capacidad se calcula **excluyendo el propio ítem**
(biserial "corregida"): si no, la pregunta se correlaciona consigo misma y el
resultado sale inflado.

⚠️ NECESITA ESCALA
------------------
Con 2 alumnos esto no dice nada: no hay variabilidad de capacidad que correlacionar.
Madura con decenas de alumnos (una academia). El umbral vive en BD
(`min_respuestas_discriminacion`) para poder calibrarlo.

Uso:
  python3 scripts/analisis_items.py --supabase --dry-run
  python3 scripts/analisis_items.py --supabase
"""

import sys
import argparse
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._supabase_env import load_supabase_secrets, use_local_defaults

# Por debajo de esto, la pregunta no distingue a nadie
_UMBRAL_NO_DISCRIMINA = 0.10

# Para marcar la alerta GRAVE hace falta una discriminación claramente negativa,
# no un simple valor bajo cero. Con muestras pequeñas, una correlación de -0.02
# es RUIDO, no un defecto: marcarla como "clave sospechosa" haría que el editor
# revisara preguntas sanas y acabara ignorando las alertas. Un detector que grita
# "lobo" no sirve para nada.
_UMBRAL_CLAVE_SOSPECHOSA = -0.10


def _biserial(pares: list[tuple[int, float]]) -> float | None:
    """
    Correlación de Pearson entre acierto (0/1) y capacidad del alumno.
    Devuelve None si no hay varianza (todos aciertan, o todos tienen la misma
    capacidad): en ese caso la correlación no está definida.
    """
    n = len(pares)
    if n < 2:
        return None
    mx = sum(p[0] for p in pares) / n
    my = sum(p[1] for p in pares) / n
    sxy = sum((x - mx) * (y - my) for x, y in pares)
    sxx = sum((x - mx) ** 2 for x, _ in pares)
    syy = sum((y - my) ** 2 for _, y in pares)
    if sxx == 0 or syy == 0:
        return None
    return sxy / (sxx * syy) ** 0.5


def run(dry_run: bool = False) -> None:
    from app.db import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(MAX(min_respuestas_discriminacion), 20)
                FROM normas.parametros_aprendizaje WHERE oposicion_id = 1
            """)
            min_n = cur.fetchone()[0]

            # Los blancos por reloj quedan fuera (migración 052): quien no llegó a
            # la pregunta no la falló, no la leyó. Contarlos haría que las
            # preguntas del FINAL del examen —a las que menos gente llega—
            # parecieran imposibles, y el detector señalaría preguntas sanas
            # por su posición.
            cur.execute("""
                SELECT r.user_id, r.pregunta_id, r.opcion_elegida, r.correcta
                FROM normas.respuestas r
                JOIN normas.preguntas_test pt ON pt.pregunta_id = r.pregunta_id
                WHERE pt.revisada AND pt.activa AND NOT pt.descartada
                  AND NOT r.blanco_por_tiempo
            """)
            respuestas = cur.fetchall()

            cur.execute("""
                SELECT pregunta_id, correcta FROM normas.preguntas_test
                WHERE revisada AND activa AND NOT descartada
            """)
            clave = dict(cur.fetchall())

    if not respuestas:
        print("No hay respuestas registradas todavía (migración 048).")
        print("Este análisis necesita alumnos: con el banco vacío de respuestas no dice nada.")
        return

    # Totales por alumno, para calcular la capacidad
    tot = defaultdict(int)
    aci = defaultdict(int)
    for uid, pid, _op, ok in respuestas:
        tot[uid] += 1
        aci[uid] += 1 if ok else 0

    por_pregunta = defaultdict(list)
    elecciones   = defaultdict(lambda: defaultdict(int))
    for uid, pid, op, ok in respuestas:
        por_pregunta[pid].append((uid, ok))
        elecciones[pid][op] += 1        # op = None -> en blanco

    print(f"Respuestas registradas: {len(respuestas)}  ·  alumnos: {len(tot)}")
    print(f"Umbral para fiarse de la discriminación: {min_n} respuestas\n")

    resultados = []
    for pid, lista in por_pregunta.items():
        n = len(lista)
        if n < min_n:
            continue

        # Capacidad CORREGIDA: se excluye este propio ítem del total del alumno.
        pares = []
        for uid, ok in lista:
            otras_tot = tot[uid] - 1
            otras_aci = aci[uid] - (1 if ok else 0)
            if otras_tot <= 0:
                continue
            pares.append((1 if ok else 0, otras_aci / otras_tot))

        d = _biserial(pares)

        k = clave.get(pid)
        conteo = elecciones[pid]
        n_correcta = conteo.get(k, 0)
        distractor_gana = any(
            o != k and conteo.get(o, 0) > n_correcta for o in "abcd"
        )
        muertos = [o for o in "abcd" if o != k and conteo.get(o, 0) == 0]

        # Prioridad de la alerta: lo grave primero
        alerta = None
        if (d is not None and d < _UMBRAL_CLAVE_SOSPECHOSA) or distractor_gana:
            alerta = "clave_sospechosa"
        elif d is not None and d < _UMBRAL_NO_DISCRIMINA:
            alerta = "no_discrimina"
        elif muertos:
            alerta = "distractor_muerto"

        resultados.append((pid, d, n, alerta, dict(conteo), k))

    if not resultados:
        print(f"Ninguna pregunta alcanza aún las {min_n} respuestas. Nada que analizar.")
        print("(Es lo esperado hasta que haya alumnos de verdad.)")
        return

    alertas = defaultdict(list)
    for pid, d, n, alerta, conteo, k in resultados:
        if alerta:
            alertas[alerta].append((pid, d, n, conteo, k))

    print(f"Preguntas analizadas: {len(resultados)}\n")
    etiquetas = {
        "clave_sospechosa":  "🔴 CLAVE SOSPECHOSA (revisar YA: puede estar mal marcada)",
        "no_discrimina":     "🟡 NO DISCRIMINA (no distingue al que sabe del que no)",
        "distractor_muerto": "⚪ DISTRACTOR MUERTO (una opción no la elige nadie)",
    }
    for tipo, etiqueta in etiquetas.items():
        items = alertas.get(tipo, [])
        print(f"{etiqueta}: {len(items)}")
        for pid, d, n, conteo, k in items[:5]:
            dd = f"{d:+.2f}" if d is not None else "n/d"
            reparto = " ".join(f"{o or 'blanco'}:{c}" for o, c in sorted(
                conteo.items(), key=lambda x: (x[0] is None, x[0])))
            print(f"     id={pid}  discriminación={dd}  n={n}  clave={k}  [{reparto}]")
        print()

    if not dry_run:
        with get_connection() as conn:
            with conn.cursor() as cur:
                for pid, d, n, alerta, _c, _k in resultados:
                    cur.execute("""
                        UPDATE normas.preguntas_test
                           SET discriminacion = %s, discriminacion_n = %s,
                               alerta_calidad = %s
                         WHERE pregunta_id = %s
                    """, (d, n, alerta, pid))
            conn.commit()
        print("Guardado en preguntas_test (discriminacion / alerta_calidad).")
    else:
        print("DRY-RUN: no se ha escrito nada.")


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
