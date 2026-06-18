"""
Pipeline Q&A:
  pregunta → embedding → búsqueda semántica → prompt → Claude → respuesta
"""

import os
import anthropic
from app.config import CLAUDE_MODEL
from app.retrieval import embed_query, search_articles


def _build_prompt(pregunta: str, articulos: list[dict]) -> list[dict]:
    contexto = "\n\n".join(
        f"[{a['tipo'].capitalize()} {a['numero']}]\n{a['contenido']}"
        for a in articulos
    )
    return [
        {
            "role": "user",
            "content": (
                f"Eres un asistente jurídico especializado en la Constitución Española.\n"
                f"Responde a la pregunta basándote únicamente en los artículos proporcionados.\n"
                f"Cita siempre el número de artículo que respalda cada afirmación.\n\n"
                f"ARTÍCULOS RELEVANTES:\n{contexto}\n\n"
                f"PREGUNTA: {pregunta}"
            ),
        }
    ]


def run_qa(pregunta: str) -> str:
    vector    = embed_query(pregunta)
    articulos = search_articles(vector)
    messages  = _build_prompt(pregunta, articulos)

    client   = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=messages,
    )
    return response.content[0].text
