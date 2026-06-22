"""
Capa de recuperación semántica:
  - embed_query: convierte una pregunta en vector[1536] usando OpenAI (con caché en memoria)
  - search_articles: busca los k artículos más similares en pgvector
  - get_estructura_db: devuelve metadatos estructurales reales de la CE desde la BD
"""

import os
from openai import OpenAI
from app.config import OPENAI_EMBEDDING_MODEL, TOP_K_ARTICLES
from app.db import get_connection

_embedding_cache: dict[str, list[float]] = {}


def embed_query(text: str) -> list[float]:
    if text not in _embedding_cache:
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=text)
        _embedding_cache[text] = response.data[0].embedding
    return _embedding_cache[text]


def get_titulos_db() -> list[dict]:
    """Devuelve la lista de títulos con su id, número y denominación."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT titulo_id, numero, denominacion
                FROM legislacion.titulos
                ORDER BY orden
            """)
            return [{"titulo_id": r[0], "numero": r[1], "denominacion": r[2]}
                    for r in cur.fetchall()]


def get_articulos_por_titulo(titulo_id: int) -> list[dict]:
    """Recupera todos los artículos de un título ordenados por posición."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT numero, tipo, contenido
                FROM legislacion.articulos
                WHERE titulo_id = %s AND tipo = 'articulo'
                ORDER BY orden_global
            """, (titulo_id,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_estructura_db() -> dict:
    """
    Extrae metadatos estructurales de la Constitución directamente desde la BD.
    Devuelve conteos y listados de títulos, capítulos, secciones y artículos.
    """
    with get_connection() as conn:
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


def search_articles(vector: list[float], k: int = TOP_K_ARTICLES) -> list[dict]:
    """
    Devuelve los k artículos más cercanos al vector dado (similitud coseno).
    Cada resultado incluye: numero, tipo, contenido, similitud.
    """
    with get_connection() as conn:
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
