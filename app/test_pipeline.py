"""
Pipeline de generación de preguntas tipo test:
  filtro → fetch artículos → prompt → Claude → JSON con pregunta + opciones
"""

import os
import json
import anthropic
from app.config import CLAUDE_MODEL
from app.db import get_connection


def fetch_articles(titulo_id: int | None = None,
                   capitulo_id: int | None = None,
                   n: int = 5) -> list[dict]:
    """
    Recupera artículos reales de la Constitución para generar tests.
    Sin filtro → selección aleatoria entre todos los artículos.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if titulo_id:
                cur.execute("""
                    SELECT numero, tipo, contenido
                    FROM legislacion.articulos
                    WHERE titulo_id = %s AND tipo = 'articulo'
                    ORDER BY orden_global
                    LIMIT %s
                """, (titulo_id, n))
            elif capitulo_id:
                cur.execute("""
                    SELECT numero, tipo, contenido
                    FROM legislacion.articulos
                    WHERE capitulo_id = %s AND tipo = 'articulo'
                    ORDER BY orden_global
                    LIMIT %s
                """, (capitulo_id, n))
            else:
                cur.execute("""
                    SELECT numero, tipo, contenido
                    FROM legislacion.articulos
                    WHERE tipo = 'articulo'
                    ORDER BY RANDOM()
                    LIMIT %s
                """, (n,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def _build_test_prompt(articulo: dict) -> list[dict]:
    return [
        {
            "role": "user",
            "content": (
                f"Eres un experto en Derecho Constitucional español y creador de exámenes.\n"
                f"A partir del siguiente artículo de la Constitución Española, genera UNA pregunta "
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


def run_gentest(titulo_id: int | None = None,
                capitulo_id: int | None = None,
                n: int = 5) -> list[dict]:
    articulos = fetch_articles(titulo_id=titulo_id, capitulo_id=capitulo_id, n=n)
    client    = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    results   = []

    for art in articulos:
        messages = _build_test_prompt(art)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            messages=messages,
        )
        try:
            raw = response.content[0].text.strip()
            # Claude a veces envuelve la respuesta en ```json ... ```
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            parsed = json.loads(raw)
            results.append(parsed)
        except json.JSONDecodeError:
            results.append({"articulo": art["numero"], "error": "respuesta no parseable", "raw": response.content[0].text[:200]})

    return results
