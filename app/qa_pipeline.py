"""
Pipeline Q&A con enrutamiento inteligente:
  - Clasificador Claude → ESTRUCTURAL | CONTENIDO
  - ESTRUCTURAL: consulta directa a la BD (metadatos reales)
  - CONTENIDO:   embedding → búsqueda semántica → Claude
"""

import os
import anthropic
from app.config import CLAUDE_MODEL
from app.retrieval import embed_query, search_articles, get_estructura_db


def _clasificar_pregunta(pregunta: str, client: anthropic.Anthropic) -> str:
    """
    Devuelve 'ESTRUCTURAL' si la pregunta es sobre la organización o
    composición del texto constitucional (número de títulos, artículos,
    capítulos, disposiciones, etc.).
    Devuelve 'CONTENIDO' para cualquier pregunta sobre el fondo jurídico.
    """
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": (
                "Clasifica la siguiente pregunta sobre la Constitución Española.\n"
                "Responde ÚNICAMENTE con una de estas dos palabras, sin explicación:\n"
                "- ESTRUCTURAL: si pregunta por la organización del documento "
                "(número de títulos, artículos, capítulos, secciones, disposiciones, "
                "cómo está estructurada, cuántos elementos tiene, etc.)\n"
                "- CONTENIDO: si pregunta por el fondo jurídico, los derechos, "
                "las instituciones, lo que dice un artículo concreto, etc.\n\n"
                f"Pregunta: {pregunta}"
            ),
        }],
    )
    clasificacion = response.content[0].text.strip().upper()
    return "ESTRUCTURAL" if "ESTRUCTURAL" in clasificacion else "CONTENIDO"


def _responder_estructural(pregunta: str, client: anthropic.Anthropic) -> str:
    """
    Responde preguntas estructurales usando datos reales extraídos de la BD.
    Claude recibe los metadatos exactos y solo tiene que redactar la respuesta.
    """
    estructura = get_estructura_db()

    titulos_lista = "\n".join(
        f"  - {t['numero']}: {t['nombre']}" for t in estructura["titulos"]
    )

    contexto = (
        f"DATOS REALES DE LA CONSTITUCIÓN ESPAÑOLA (extraídos de la base de datos):\n\n"
        f"Número de títulos: {estructura['n_titulos']}\n"
        f"Títulos:\n{titulos_lista}\n\n"
        f"Número de capítulos: {estructura['n_capitulos']}\n"
        f"Número de secciones: {estructura['n_secciones']}\n"
        f"Número de artículos: {estructura['n_articulos']}\n"
        f"Número de disposiciones: {estructura['n_disposiciones']}\n"
        f"Total de elementos: {estructura['n_total']}\n"
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": (
                "Eres un asistente jurídico especializado en la Constitución Española.\n"
                "Responde la pregunta usando ÚNICAMENTE los datos proporcionados a continuación. "
                "Son datos exactos extraídos de la base de datos oficial.\n\n"
                f"{contexto}\n"
                f"PREGUNTA: {pregunta}"
            ),
        }],
    )
    return response.content[0].text


def _responder_contenido(pregunta: str, client: anthropic.Anthropic) -> str:
    """
    Responde preguntas de contenido jurídico mediante RAG:
    embedding → búsqueda semántica → Claude con artículos como contexto.
    """
    vector    = embed_query(pregunta)
    articulos = search_articles(vector)

    contexto = "\n\n".join(
        f"[{a['tipo'].capitalize()} {a['numero']}]\n{a['contenido']}"
        for a in articulos
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                "Eres un asistente jurídico especializado en la Constitución Española.\n"
                "Responde a la pregunta basándote únicamente en los artículos proporcionados.\n"
                "Cita siempre el número de artículo que respalda cada afirmación.\n\n"
                f"ARTÍCULOS RELEVANTES:\n{contexto}\n\n"
                f"PREGUNTA: {pregunta}"
            ),
        }],
    )
    return response.content[0].text


def run_qa(pregunta: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    tipo   = _clasificar_pregunta(pregunta, client)

    if tipo == "ESTRUCTURAL":
        return _responder_estructural(pregunta, client)
    else:
        return _responder_contenido(pregunta, client)
