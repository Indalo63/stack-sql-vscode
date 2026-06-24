"""
Pipeline Q&A con enrutamiento inteligente de tres vías:
  - Clasificador Claude → ESTRUCTURAL | RESUMEN | CONTENIDO
  - ESTRUCTURAL: metadatos de la BD (conteos, listados de títulos)
  - RESUMEN:     todos los artículos de un título desde la BD → Claude
  - CONTENIDO:   embedding → búsqueda semántica → Claude
"""

import os
import re
import anthropic
from app.config import CLAUDE_MODEL, ANTHROPIC_API_KEY
from app.config import SIMILARITY_THRESHOLD, TOKEN_THRESHOLD_HIERARCHICAL
from app.retrieval import (
    embed_query, search_articles, search_articles_hierarchical,
    get_estructura_db, get_titulos_db, get_articulos_por_titulo, get_ley_info,
)


def _clasificar_pregunta(pregunta: str, ley_nombre: str,
                          client: anthropic.Anthropic) -> str:
    """
    Clasifica la pregunta en uno de tres tipos:
    - ESTRUCTURAL: cantidades o nombres de elementos del documento
    - RESUMEN:     resumen o descripción del contenido de un título o capítulo
    - CONTENIDO:   pregunta jurídica sobre el fondo de un tema concreto
    """
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=15,
        messages=[{
            "role": "user",
            "content": (
                f"Clasifica la siguiente pregunta sobre {ley_nombre}.\n"
                "Responde ÚNICAMENTE con una de estas tres palabras, sin explicación:\n\n"
                "- ESTRUCTURAL: pregunta solo por cantidades o nombres de elementos. "
                "Ejemplos: '¿Cuántos títulos tiene?', '¿Cuántos artículos hay?', "
                "'¿Qué títulos existen?', '¿Cuántos capítulos tiene el Título I?'\n\n"
                "- RESUMEN: pide resumir, describir o explicar el contenido completo "
                "de un título o capítulo entero. "
                "Ejemplos: 'Resume el Título I', '¿Qué regula el Título VIII?', "
                "'Explica el contenido del Título II', '¿De qué trata el Título X?'\n\n"
                "- CONTENIDO: pregunta jurídica concreta sobre derechos, instituciones, "
                "procedimientos o lo que dice un artículo específico. "
                "Ejemplos: '¿Qué dice el artículo 14?', '¿Cómo se aprueba una ley?', "
                "'¿Qué derechos reconoce?', '¿Qué es el Tribunal Constitucional?'\n\n"
                f"Pregunta: {pregunta}"
            ),
        }],
    )
    texto = response.content[0].text.strip().upper()
    if "ESTRUCTURAL" in texto:
        return "ESTRUCTURAL"
    if "RESUMEN" in texto:
        return "RESUMEN"
    return "CONTENIDO"


def _extraer_titulo_id(pregunta: str, ley_id: int, ley_nombre: str,
                        client: anthropic.Anthropic) -> int | None:
    """
    Extrae el titulo_id de la BD a partir de la mención en la pregunta.
    Usa la lista real de títulos de la ley para el mapeo.
    """
    titulos = get_titulos_db(ley_id)
    lista   = "\n".join(
        f"  titulo_id={t['titulo_id']} → Título {t['numero']}: {t['denominacion']}"
        for t in titulos
    )
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": (
                f"Dada la siguiente lista de títulos de {ley_nombre}:\n"
                f"{lista}\n\n"
                "¿Qué titulo_id corresponde al título mencionado en esta pregunta?\n"
                "Responde ÚNICAMENTE con el número entero del titulo_id, sin texto adicional.\n"
                f"Pregunta: {pregunta}"
            ),
        }],
    )
    texto = response.content[0].text.strip()
    match = re.search(r"\d+", texto)
    return int(match.group()) if match else None


def _responder_resumen(pregunta: str, ley_id: int, ley_nombre: str,
                        client: anthropic.Anthropic) -> str:
    """
    Recupera TODOS los artículos del título mencionado y genera un resumen completo.
    """
    titulo_id = _extraer_titulo_id(pregunta, ley_id, ley_nombre, client)
    if titulo_id is None:
        return _responder_contenido(pregunta, ley_id, ley_nombre, client)

    titulos   = {t["titulo_id"]: t for t in get_titulos_db(ley_id)}
    articulos = get_articulos_por_titulo(titulo_id)

    if not articulos:
        return _responder_contenido(pregunta, ley_id, ley_nombre, client)

    titulo_info = titulos.get(titulo_id, {})
    contexto = "\n\n".join(
        f"[Artículo {a['numero']}]\n{a['contenido']}"
        for a in articulos
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": (
                f"Eres un asistente jurídico especializado en {ley_nombre}.\n"
                f"A continuación tienes el texto íntegro del "
                f"Título {titulo_info.get('numero', '')} — "
                f"{titulo_info.get('denominacion', '')} "
                f"({len(articulos)} artículos).\n"
                "Elabora un resumen estructurado que explique qué regula este título, "
                "sus principales bloques temáticos y los derechos o instituciones más relevantes. "
                "Cita los artículos clave al mencionar cada bloque.\n\n"
                f"TEXTO DEL TÍTULO:\n{contexto}\n\n"
                f"PREGUNTA: {pregunta}"
            ),
        }],
    )
    return response.content[0].text


def _responder_estructural(pregunta: str, ley_id: int, ley_nombre: str,
                            client: anthropic.Anthropic) -> str:
    """Responde preguntas de cantidad/estructura con datos exactos de la BD."""
    estructura  = get_estructura_db(ley_id)
    titulos_txt = "\n".join(
        f"  - Título {t['numero']}: {t['nombre']}" for t in estructura["titulos"]
    )
    contexto = (
        f"DATOS REALES DE {ley_nombre.upper()} (extraídos de la base de datos):\n\n"
        f"Número de títulos: {estructura['n_titulos']}\n"
        f"Títulos:\n{titulos_txt}\n\n"
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
                f"Eres un asistente jurídico especializado en {ley_nombre}.\n"
                "Responde la pregunta usando ÚNICAMENTE los datos proporcionados. "
                "Son datos exactos extraídos de la base de datos oficial.\n"
                "IMPORTANTE: responde solo lo que se pregunta, sin añadir datos no solicitados.\n\n"
                f"{contexto}\n"
                f"PREGUNTA: {pregunta}"
            ),
        }],
    )
    return response.content[0].text


def _responder_contenido(pregunta: str, ley_id: int, ley_nombre: str,
                          client: anthropic.Anthropic,
                          usar_jerarquico: bool = False) -> str:
    """Responde preguntas jurídicas concretas mediante RAG semántico."""
    vector = embed_query(pregunta)

    if usar_jerarquico:
        articulos = search_articles_hierarchical(
            vector, ley_id, min_similarity=SIMILARITY_THRESHOLD)
    else:
        articulos = search_articles(
            vector, ley_id, min_similarity=SIMILARITY_THRESHOLD)

    if not articulos:
        return "No se han encontrado artículos relevantes para esta pregunta en la ley seleccionada."

    contexto = "\n\n".join(
        f"[{a['tipo'].capitalize()} {a['numero']}] (similitud: {a['similitud']:.2f})\n{a['contenido']}"
        for a in articulos
    )
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                f"Eres un asistente jurídico especializado en {ley_nombre}.\n"
                "Responde a la pregunta basándote ÚNICAMENTE en los artículos proporcionados.\n"
                "Cita siempre el número de artículo (art. X) que respalda cada afirmación.\n"
                "Si la información necesaria no está en los artículos, indícalo explícitamente.\n\n"
                f"ARTÍCULOS RELEVANTES:\n{contexto}\n\n"
                f"PREGUNTA: {pregunta}"
            ),
        }],
    )
    return response.content[0].text


def run_qa(pregunta: str, ley_id: int) -> str:
    ley    = get_ley_info(ley_id)
    nombre = ley["nombre"]
    tokens = ley.get("token_count") or 0
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    tipo   = _clasificar_pregunta(pregunta, nombre, client)

    usar_jerarquico = tokens >= TOKEN_THRESHOLD_HIERARCHICAL

    if tipo == "ESTRUCTURAL":
        return _responder_estructural(pregunta, ley_id, nombre, client)
    if tipo == "RESUMEN":
        return _responder_resumen(pregunta, ley_id, nombre, client)
    return _responder_contenido(pregunta, ley_id, nombre, client, usar_jerarquico)
