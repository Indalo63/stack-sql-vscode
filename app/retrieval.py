"""
Capa de recuperación semántica:
  - embed_query: convierte una pregunta en vector[1536] usando OpenAI
  - search_articles: busca los k artículos más similares en pgvector
"""

import os
from openai import OpenAI
from app.config import OPENAI_EMBEDDING_MODEL, TOP_K_ARTICLES
from app.db import get_connection


def embed_query(text: str) -> list[float]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def search_articles(vector: list[float], k: int = TOP_K_ARTICLES) -> list[dict]:
    """
    Devuelve los k artículos más cercanos al vector dado (similitud coseno).
    Cada resultado incluye: numero, tipo, contenido, similitud.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    a.numero,
                    a.tipo,
                    a.contenido,
                    1 - (a.embedding <=> %s::vector) AS similitud
                FROM legislacion.articulos a
                WHERE a.embedding IS NOT NULL
                ORDER BY a.embedding <=> %s::vector
                LIMIT %s
            """, (vector, vector, k))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()
