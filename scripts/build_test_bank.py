"""
scripts/build_test_bank.py

Genera preguntas tipo test en lote y las guarda en normas.preguntas_test.
Las preguntas se guardan con revisada=FALSE hasta que el formador las apruebe.

Mejoras respecto a la versión original:
  - Few-shot con preguntas oficiales verificadas (mismo estilo que el examen real)
  - Detección de apartados numerados → cita el apartado concreto en el enunciado
  - Instrucción para mezclar respuestas literales y reformuladas (como en GACE real)
  - Prioriza artículos que ya han aparecido en exámenes oficiales

Uso:
  # Contra Docker local
  python3 scripts/build_test_bank.py --ley-id 1 --n 3 --dry-run

  # Contra Supabase desde WSL2 (Session Pooler IPv4)
  python3 scripts/build_test_bank.py --supabase --ley-id 1 --n 3 --dry-run
  python3 scripts/build_test_bank.py --supabase --n 50   # todas las leyes

Coste estimado: ~0,012 € por pregunta (Claude Sonnet 4.6 con few-shot)
"""

import os
import re
import sys
import json
import time
import random
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

MIN_LENGTH = 200


# ── Carga de credenciales ─────────────────────────────────────────────────────

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

    print(f"Supabase via Session Pooler: {os.environ['DB_HOST']} / {os.environ['DB_USER']}")


# ── Consultas BD ──────────────────────────────────────────────────────────────

def _get_leyes(ley_id=None):
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            sql = "SELECT ley_id, nombre FROM normas.leyes WHERE activa = TRUE"
            params = ()
            if ley_id:
                sql += " AND ley_id = %s"
                params = (ley_id,)
            cur.execute(sql + " ORDER BY ley_id", params)
            return [{"ley_id": r[0], "nombre": r[1]} for r in cur.fetchall()]


def _fetch_articles(ley_id, n, max_por_articulo=1):
    """
    Artículos candidatos para generación:
    - Excluye artículos que ya tienen >= max_por_articulo preguntas IA (pendientes + aprobadas).
    - Marca con examinado=True los que aparecieron en exámenes oficiales (indicador ★).
    - Ordena por longitud de contenido ponderada aleatoriamente (cobertura uniforme).
    """
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.numero, a.titulo_id, a.contenido, t.denominacion AS titulo_nombre,
                       EXISTS (
                           SELECT 1 FROM normas.preguntas_test p
                           WHERE p.ley_id = a.ley_id
                             AND p.articulo = a.numero
                             AND p.fuente IN ('oficial_2024', 'oficial_2025')
                       ) AS examinado
                FROM normas.articulos a
                LEFT JOIN normas.titulos t ON t.titulo_id = a.titulo_id
                WHERE a.ley_id = %s
                  AND a.tipo = 'articulo'
                  AND length(a.contenido) >= %s
                  AND a.contenido !~* '\\(derogado|sin contenido|suprimido\\)'
                  AND (
                      SELECT COUNT(*) FROM normas.preguntas_test p
                      WHERE p.ley_id = a.ley_id
                        AND p.articulo = a.numero
                        AND p.fuente = 'ia'
                  ) < %s
                ORDER BY RANDOM() * log(length(a.contenido)) DESC
                LIMIT %s
            """, (ley_id, MIN_LENGTH, max_por_articulo, n))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetch_few_shots(ley_id, n=2):
    """
    Carga n preguntas oficiales verificadas para usar como few-shot.
    Prefiere ejemplos de la misma ley; si no hay suficientes, usa de cualquier ley.
    Excluye preguntas con sub-artículos (11.3) y sin número (S/N).
    El JOIN con articulos es LEFT JOIN para evitar descartar preguntas cuyo número
    de artículo no coincide exactamente con articulos.numero (discrepancias de formato).
    """
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.pregunta, p.opcion_a, p.opcion_b, p.opcion_c, p.opcion_d,
                       p.correcta, p.articulo,
                       COALESCE(a.contenido, '') AS contenido,
                       l.nombre
                FROM normas.preguntas_test p
                JOIN normas.leyes l ON l.ley_id = p.ley_id
                LEFT JOIN normas.articulos a
                  ON a.ley_id = p.ley_id
                 AND a.numero = p.articulo
                 AND a.tipo   = 'articulo'
                WHERE p.revisada = TRUE
                  AND p.fuente IN ('oficial_2024', 'oficial_2025')
                  AND p.articulo IS NOT NULL
                  AND p.articulo NOT IN ('S/N', 's/n')
                  AND p.articulo NOT LIKE '%%.%%'
                ORDER BY (p.ley_id = %s) DESC, RANDOM()
                LIMIT %s
            """, (ley_id, n))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _save(ley_id, art, parsed, epigrafe_id=None):
    from app.db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO normas.preguntas_test
                    (ley_id, titulo_id, articulo, pregunta,
                     opcion_a, opcion_b, opcion_c, opcion_d,
                     correcta, explicacion, fuente, epigrafe_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ia', %s)
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
                epigrafe_id,
            ))
        conn.commit()


# ── Construcción del prompt ───────────────────────────────────────────────────

def _has_numbered_paragraphs(contenido):
    """Detecta si el artículo tiene apartados numerados (1., 2. o 1) 2))."""
    return bool(re.search(r'^\s*\d+[.)]\s', contenido, re.MULTILINE))


def _format_few_shot(fs):
    """Formatea un ejemplo official para incluirlo en el prompt."""
    opts = "\n".join(
        f"  {k}) {fs[f'opcion_{k}']}"
        for k in ("a", "b", "c", "d")
    )
    extracto = fs["contenido"][:350]
    if len(fs["contenido"]) > 350:
        extracto += "..."
    return (
        f"[Artículo {fs['articulo']} de {fs['nombre']}]\n"
        f"{extracto}\n\n"
        f"→ Pregunta oficial:\n"
        f"{fs['pregunta']}\n"
        f"{opts}\n"
        f"Correcta: {fs['correcta']}"
    )


def _build_prompt(art, ley_nombre, few_shots=None, tiene_apartados=False, epigrafes=None):

    # Bloque de few-shot
    few_shots_block = ""
    if few_shots:
        ejemplos = "\n\n---\n\n".join(_format_few_shot(fs) for fs in few_shots)
        few_shots_block = (
            "EJEMPLOS DE PREGUNTAS OFICIALES GACE "
            "(úsalos como referencia exacta de estilo y dificultad):\n\n"
            f"{ejemplos}\n\n"
            "──────────────────────────────────────\n\n"
        )

    reglas = [
        f"El enunciado DEBE comenzar con 'Según el artículo [número] de "
        f"{ley_nombre},' o 'De acuerdo con el artículo [número] de {ley_nombre},'",
        "Opciones en a), b), c), d) minúsculas.",
        "Distractores con error sutil y técnico: plazo distinto, porcentaje "
        "diferente, órgano incorrecto o palabra clave cambiada. Nunca distractores "
        "conceptualmente muy distintos.",
        "Nivel alto: datos exactos (plazos, porcentajes, órganos, requisitos), "
        "no conceptos generales.",
        "Sin símbolos matemáticos. Escribir en texto: 'igual a', 'mayor que', "
        "'porcentaje', etc.",
    ]
    if tiene_apartados:
        reglas.append(
            f"El artículo tiene apartados numerados. Cita el apartado concreto "
            f"en el enunciado: 'el apartado X del artículo {art['numero']}' "
            f"o 'el artículo {art['numero']}.X'."
        )
    reglas.append(
        "La opción correcta puede citar textualmente la norma "
        "O parafrasearla con otras palabras (ambos estilos aparecen en exámenes "
        "oficiales GACE). Lo importante es que sea inequívocamente correcta."
    )
    if epigrafes:
        reglas.append(
            "Indica en el campo \"tema\" el número del tema del temario oficial "
            "(listado más abajo) al que pertenece esta pregunta, según el artículo "
            "concreto sobre el que trata."
        )
    reglas_txt = "\n".join(f"{i}. {r}" for i, r in enumerate(reglas, 1))

    temas_block = ""
    tema_campo = ""
    if epigrafes:
        temas_txt = "\n".join(f"{e['tema']}. {e['titulo']}" for e in epigrafes)
        titulo_ctx = (
            f"El artículo pertenece al Título \"{art['titulo_nombre']}\" de {ley_nombre}.\n"
            if art.get("titulo_nombre") else ""
        )
        temas_block = (
            f"\n{titulo_ctx}"
            f"TEMAS DEL BLOQUE (temario oficial de la oposición):\n{temas_txt}\n"
        )
        tema_campo = ',"tema":N'

    return [{
        "role": "user",
        "content": (
            f"Eres un experto en Derecho español y creador de exámenes de oposición al "
            f"Cuerpo de Gestión de la Administración Civil del Estado (GACE).\n\n"
            f"A partir del siguiente artículo de {ley_nombre}, genera UNA pregunta tipo "
            f"test con exactamente 4 opciones (a, b, c, d), siguiendo el estilo oficial "
            f"del examen GACE.\n\n"
            f"{few_shots_block}"
            f"REGLAS DE ESTILO OBLIGATORIAS:\n"
            f"{reglas_txt}\n"
            f"\nARTÍCULO {art['numero']}:\n{art['contenido']}\n"
            f"{temas_block}\n"
            f"Responde SOLO con JSON válido, sin texto adicional:\n"
            f'{{"articulo":"{art["numero"]}","pregunta":"...","opciones":'
            f'{{"a":"...","b":"...","c":"...","d":"..."}},'
            f'"correcta":"a","explicacion":"..."{tema_campo}}}'
        ),
    }]


# ── Runner principal ──────────────────────────────────────────────────────────

def run(ley_id=None, n=50, dry_run=False, delay=0.5, max_por_articulo=1, oposicion="GACE"):
    import anthropic
    from app.config import CLAUDE_MODEL, ANTHROPIC_API_KEY
    from app.retrieval import get_bloque_y_epigrafes

    leyes = _get_leyes(ley_id)
    if not leyes:
        print("No se encontraron leyes activas.")
        return

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    total_ok = total_err = 0

    for ley in leyes:
        print(f"\n{'─' * 60}")
        print(f"Ley: {ley['nombre']}  (id={ley['ley_id']})")

        arts = _fetch_articles(ley["ley_id"], n, max_por_articulo)
        if not arts:
            print("  Sin artículos nuevos que procesar.")
            continue

        try:
            few_shots = _fetch_few_shots(ley["ley_id"])
        except Exception as e:
            print(f"  AVISO: no se pudieron cargar few-shots ({e}). Se continúa sin ellos.")
            few_shots = []

        bloque, epigrafes = get_bloque_y_epigrafes(ley["ley_id"], oposicion_codigo=oposicion)
        temas_validos = {e["tema"] for e in epigrafes} if epigrafes else None

        examinados = sum(1 for a in arts if a.get("examinado"))
        print(f"  Artículos a generar : {len(arts)}  "
              f"(examinados en GACE: {examinados})")
        print(f"  Few-shot examples   : {len(few_shots)}")
        print(f"  Bloque / epígrafes  : {bloque or '(sin bloque asignado)'} "
              f"({len(epigrafes)} temas)")

        ok = err = 0
        for i, art in enumerate(arts, 1):
            tiene_apartados = _has_numbered_paragraphs(art["contenido"])
            try:
                resp = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=800,
                    messages=_build_prompt(art, ley["nombre"],
                                          few_shots=few_shots,
                                          tiene_apartados=tiene_apartados,
                                          epigrafes=epigrafes),
                )
                parsed = _parse_and_validate(resp.content[0].text, temas_validos=temas_validos)

                epigrafe_id = None
                if epigrafes and "tema" in parsed:
                    epigrafe_id = next(
                        e["epigrafe_id"] for e in epigrafes if e["tema"] == parsed["tema"]
                    )

                if not dry_run:
                    _save(ley["ley_id"], art, parsed, epigrafe_id=epigrafe_id)

                ok += 1
                tag = "[DRY]" if dry_run else "[OK] "
                examen_tag = " ★" if art.get("examinado") else ""
                apart_tag  = " [apt]" if tiene_apartados else ""
                tema_tag = f" -> {bloque}.{parsed['tema']}" if epigrafe_id else ""
                print(f"  {tag} [{i:>3}/{len(arts)}] Art. {art['numero']}{examen_tag}{apart_tag}{tema_tag}")
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


# ── Validación del JSON generado ─────────────────────────────────────────────

def _parse_and_validate(raw, temas_validos=None):
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if not m:
        raise ValueError("No se encontró JSON en la respuesta")
    parsed = json.loads(m.group())

    c = parsed.get("correcta", "").strip().lower().replace(")", "").replace(".", "")[:1]
    if c not in "abcd":
        raise ValueError(f"Valor de 'correcta' inválido: {parsed.get('correcta')!r}")
    parsed["correcta"] = c

    raw_opts = parsed.get("opciones", {})
    opts = {k.strip().lower().replace(")", "")[:1]: v for k, v in raw_opts.items()}
    if not all(k in opts for k in "abcd"):
        raise ValueError(f"Opciones incompletas: {list(opts.keys())}")
    parsed["opciones"] = opts

    if not parsed.get("pregunta"):
        raise ValueError("Campo 'pregunta' vacío")

    if temas_validos is not None:
        try:
            tema = int(parsed.get("tema"))
        except (TypeError, ValueError):
            raise ValueError(f"Valor de 'tema' inválido: {parsed.get('tema')!r}")
        if tema not in temas_validos:
            raise ValueError(f"Tema {tema} no pertenece al bloque (válidos: {sorted(temas_validos)})")
        parsed["tema"] = tema

    return _barajar_opciones(parsed)


_RE_OPCION = re.compile(r'(?<![\d.])\b([abcd])\)')


def _barajar_opciones(parsed):
    """
    Baraja las opciones y remapea la respuesta correcta.

    POR QUÉ: el modelo coloca la respuesta correcta en la "a" de forma
    abrumadora. Medido el 12/07/2026 sobre las 88 primeras preguntas generadas:
    **86,4% en la "a"** (el examen oficial real: 27,8%). Sin barajar, el alumno
    aprende "ante la duda, marca la a", acierta SIN saber la ley, y eso además
    corrompe nuestras métricas (dominio, dificultad, "¿estoy listo?"), que
    estarían midiendo a alguien que adivina el patrón.

    También se remapean las letras dentro de la explicación: el modelo escribe
    cosas como "la opción b) es incorrecta porque…", y barajar sin tocar ese
    texto lo dejaría señalando a la opción equivocada. Las referencias a
    artículos ("artículo 10.2.c)") NO se tocan: el patrón exige que la letra no
    vaya precedida de dígito ni punto.
    """
    letras = ["a", "b", "c", "d"]
    ops = parsed["opciones"]
    correcta = parsed["correcta"]

    destino = random.choice(letras)                       # dónde va la correcta
    libres  = [l for l in letras if l != destino]
    otras   = [l for l in letras if l != correcta]
    random.shuffle(libres)
    mapa = {correcta: destino}
    mapa.update(dict(zip(otras, libres)))

    parsed["opciones"] = {mapa[k]: v for k, v in ops.items()}
    parsed["correcta"] = destino

    def _remap(txt):
        return _RE_OPCION.sub(lambda m: f"{mapa[m.group(1)]})", txt) if txt else txt

    parsed["explicacion"] = _remap(parsed.get("explicacion"))
    parsed["pregunta"]    = _remap(parsed.get("pregunta"))
    return parsed


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Genera banco de preguntas GACE")
    p.add_argument("--supabase", action="store_true",
                   help="Conectar a Supabase via Session Pooler")
    p.add_argument("--ley-id", type=int, default=None,
                   help="ID de la ley a procesar (omitir = todas las activas)")
    p.add_argument("--n", type=int, default=50,
                   help="Número de preguntas por ley (default: 50)")
    p.add_argument("--dry-run", action="store_true",
                   help="Genera preguntas pero NO las guarda en BD")
    p.add_argument("--delay", type=float, default=0.5,
                   help="Segundos entre llamadas a la API (default: 0.5)")
    p.add_argument("--max-por-articulo", type=int, default=1,
                   help="Máximo de preguntas IA por artículo, pendientes + aprobadas (default: 1)")
    p.add_argument("--oposicion", default="GACE",
                   help="Código de la oposición, para resolver bloque/epígrafes (default: GACE)")
    args = p.parse_args()

    if args.supabase:
        _load_supabase_secrets()
    else:
        os.environ.setdefault("DB_HOST",     "localhost")
        os.environ.setdefault("DB_PORT",     "5432")
        os.environ.setdefault("DB_NAME",     "stack_db")
        os.environ.setdefault("DB_USER",     "postgres")
        os.environ.setdefault("DB_PASSWORD", "postgres")

    run(ley_id=args.ley_id, n=args.n, dry_run=args.dry_run, delay=args.delay,
        max_por_articulo=args.max_por_articulo, oposicion=args.oposicion)
