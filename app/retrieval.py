"""
Capa de recuperación semántica:
  - embed_query: convierte una pregunta en vector[1536] usando OpenAI
  - search_articles: busca los k artículos más similares en pgvector
  - get_estructura_db: devuelve metadatos estructurales reales de la CE desde la BD
"""

import os
from openai import OpenAI
from app.config import OPENAI_EMBEDDING_MODEL, TOP_K_ARTICLES
from app.db import get_connection


def embed_query(text: str) -> list[float]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def get_estructura_db() -> dict:
    """
    Extrae metadatos estructurales de la Constitución directamente desde la BD.
    Devuelve conteos y listados de títulos, capítulos, secciones y artículos.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM legislacion.titulos")
            n_titulos = cur.fetchone()[0]

            cur.execute("SELECT numero, denominacion FROM legislacion.titulos ORDER BY orden")
            titulos = [{"numero": r[0], "nombre": r[1]} for r in cur.fetchall()]

            cur.execute("SELECT COUNT(*) FROM legislacion.capitulos")
            n_capitulos = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM legislacion.secciones")
            n_secciones = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM legislacion.articulos WHERE tipo = 'articulo'")
            n_articulos = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM legislacion.articulos WHERE tipo = 'disposicion'")
            n_disposiciones = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM legislacion.articulos")
            n_total = cur.fetchone()[0]

        return {
            "n_titulos": n_titulos,
            "titulos": titulos,
            "n_capitulos": n_capitulos,
            "n_secciones": n_secciones,
            "n_articulos": n_articulos,
            "n_disposiciones": n_disposiciones,
            "n_total": n_total,
        }
    finally:
        conn.close()


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
