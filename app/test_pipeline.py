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


def fetch_articles(ley_id: int,
                   titulo_id: int | None = None,
                   capitulo_id: int | None = None,
                   n: int = 5) -> list[dict]:
    """
    Recupera artículos de una ley para generar tests.
    Sin filtro de título/capítulo → selección aleatoria dentro de la ley.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if titulo_id:
                cur.execute("""
                    SELECT numero, tipo, contenido
                    FROM normas.articulos
                    WHERE ley_id = %s AND titulo_id = %s AND tipo = 'articulo'
                    ORDER BY orden_global
                    LIMIT %s
                """, (ley_id, titulo_id, n))
            elif capitulo_id:
                cur.execute("""
                    SELECT numero, tipo, contenido
                    FROM normas.articulos
                    WHERE ley_id = %s AND capitulo_id = %s AND tipo = 'articulo'
                    ORDER BY orden_global
                    LIMIT %s
                """, (ley_id, capitulo_id, n))
            else:
                cur.execute("""
                    SELECT numero, tipo, contenido
                    FROM normas.articulos
                    WHERE ley_id = %s AND tipo = 'articulo'
                    ORDER BY RANDOM()
                    LIMIT %s
                """, (ley_id, n))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _build_test_prompt(articulo: dict, ley_nombre: str) -> list[dict]:
    return [
        {
            "role": "user",
            "content": (
                f"Eres un experto en Derecho español y creador de exámenes.\n"
                f"A partir del siguiente artículo de {ley_nombre}, genera UNA pregunta "
                f"tipo test con exactamente 4 opciones (A, B, C, D).\n\n"
                f"REGLA OBLIGATORIA: No uses ningún símbolo matemático en la pregunta, las opciones "
                f"ni la explicación (quedan prohibidos: =, >, <, ≥, ≤, +, ×, ÷, %, °, →, ←, /, \\, "
                f"fracciones y cualquier otro símbolo matemático o lógico). "
                f"Escribe siempre en texto: 'igual a', 'mayor que', 'más', 'porcentaje', etc.\n\n"
                f"ARTÍCULO {articulo['numero']}:\n{articulo['contenido']}\n\n"
                f"Responde SOLO con JSON válido con esta estructura exacta:\n"
                f'{{"articulo": "{articulo["numero"]}", '
                f'"pregunta": "...", '
                f'"opciones": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, '
                f'"correcta": "A|B|C|D", '
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
