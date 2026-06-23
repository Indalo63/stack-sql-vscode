"""
Pipeline de generación de preguntas tipo test:
  filtro → fetch artículos → prompt → Claude → JSON con pregunta + opciones
"""

import os
import re
import json
import anthropic
from app.config import CLAUDE_MODEL
from app.db import get_connection


MIN_CONTENT_LENGTH = 200  # artículos con menos caracteres no generan buenas preguntas

# Patrones que indican artículos vacíos o derogados
_PATRON_VACIO = re.compile(
    r'^\s*\(?(derogado|sin contenido|suprimido|véase|ver artículo)\)?\.?\s*$',
    re.IGNORECASE
)


def fetch_articles(ley_id: int,
                   titulo_id: int | None = None,
                   capitulo_id: int | None = None,
                   n: int = 5) -> list[dict]:
    """
    Recupera artículos testables de una ley:
    - Excluye artículos con menos de MIN_CONTENT_LENGTH caracteres.
    - Excluye artículos derogados o vacíos.
    Sin filtro de título/capítulo → selección aleatoria ponderada por longitud.
    """
    filtro_contenido = f"AND length(contenido) >= {MIN_CONTENT_LENGTH} AND contenido !~* '\\\\(derogado|sin contenido|suprimido\\\\)'"
    with get_connection() as conn:
        with conn.cursor() as cur:
            if titulo_id:
                cur.execute(f"""
                    SELECT numero, tipo, contenido
                    FROM normas.articulos
                    WHERE ley_id = %s AND titulo_id = %s AND tipo = 'articulo'
                    {filtro_contenido}
                    ORDER BY orden_global
                    LIMIT %s
                """, (ley_id, titulo_id, n))
            elif capitulo_id:
                cur.execute(f"""
                    SELECT numero, tipo, contenido
                    FROM normas.articulos
                    WHERE ley_id = %s AND capitulo_id = %s AND tipo = 'articulo'
                    {filtro_contenido}
                    ORDER BY orden_global
                    LIMIT %s
                """, (ley_id, capitulo_id, n))
            else:
                # Selección aleatoria ponderada: artículos más largos tienen más probabilidad
                cur.execute(f"""
                    SELECT numero, tipo, contenido
                    FROM normas.articulos
                    WHERE ley_id = %s AND tipo = 'articulo'
                    {filtro_contenido}
                    ORDER BY RANDOM() * log(length(contenido)) DESC
                    LIMIT %s
                """, (ley_id, n))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _build_test_prompt(articulo: dict, ley_nombre: str) -> list[dict]:
    return [
        {
            "role": "user",
            "content": (
                f"Eres un experto en Derecho español y creador de exámenes de oposición al "
                f"Cuerpo de Gestión de la Administración Civil del Estado (GACE).\n\n"
                f"A partir del siguiente artículo de {ley_nombre}, genera UNA pregunta tipo "
                f"test con exactamente 4 opciones (a, b, c, d), siguiendo el estilo oficial "
                f"del examen GACE.\n\n"
                f"REGLAS DE ESTILO OBLIGATORIAS:\n"
                f"1. El enunciado DEBE comenzar con 'Según el artículo [número] de {ley_nombre},' "
                f"o 'De acuerdo con el artículo [número] de {ley_nombre},' — cita siempre la "
                f"norma completa.\n"
                f"2. Las opciones deben ser a), b), c), d) en minúsculas.\n"
                f"3. Los distractores (opciones incorrectas) deben diferir de la correcta SOLO "
                f"en datos precisos: un plazo distinto, un porcentaje diferente, un órgano "
                f"incorrecto, una palabra clave cambiada. Evita distractores conceptualmente "
                f"muy distintos; el error debe ser sutil y técnico.\n"
                f"4. Nivel de dificultad alto: pregunta por datos exactos del artículo (plazos, "
                f"porcentajes, órganos competentes, requisitos concretos), no por conceptos "
                f"generales.\n"
                f"5. No uses ningún símbolo matemático en la pregunta, las opciones ni la "
                f"explicación (prohibidos: =, >, <, más, por ciento escríbelo en texto, etc.). "
                f"Escribe siempre en texto: 'igual a', 'mayor que', 'porcentaje', etc.\n\n"
                f"ARTÍCULO {articulo['numero']}:\n{articulo['contenido']}\n\n"
                f"Responde SOLO con JSON válido con esta estructura exacta:\n"
                f'{{"articulo": "{articulo["numero"]}", '
                f'"pregunta": "...", '
                f'"opciones": {{"a": "...", "b": "...", "c": "...", "d": "..."}}, '
                f'"correcta": "a|b|c|d", '
                f'"explicacion": "..."}}'
            ),
        }
    ]


def run_gentest(ley_id: int,
                ley_nombre: str,
                titulo_id: int | None = None,
                capitulo_id: int | None = None,
                n: int = 5) -> list[dict]:
    articulos = fetch_articles(ley_id=ley_id, titulo_id=titulo_id,
                               capitulo_id=capitulo_id, n=n)
    client    = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    results   = []

    for art in articulos:
        messages = _build_test_prompt(art, ley_nombre)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            messages=messages,
        )
        try:
            raw = response.content[0].text
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not match:
                raise json.JSONDecodeError("no JSON object found", raw, 0)
            parsed = json.loads(match.group())
            results.append(parsed)
        except json.JSONDecodeError:
            results.append({
                "articulo": art["numero"],
                "error": "respuesta no parseable",
                "raw": response.content[0].text[:200],
            })

    return results
