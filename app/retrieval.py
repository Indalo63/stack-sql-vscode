"""
Capa de recuperación semántica sobre normas.*:
  - embed_query: vector[1536] con caché en memoria
  - search_articles: k artículos más similares, filtrados por ley
  - get_estructura_db: metadatos estructurales de una ley
  - get_leyes_disponibles: catálogo de leyes activas
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


def get_leyes_disponibles() -> list[dict]:
    """Lista las leyes activas disponibles en la BD."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ley_id, codigo, nombre, nombre_corto
                FROM normas.leyes
                WHERE activa = true
                ORDER BY nombre
            """)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_ley_info(ley_id: int) -> dict:
    """Devuelve metadatos de una ley (nombre, tipo, etc.)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ley_id, codigo, nombre, nombre_corto, tipo
                FROM normas.leyes
                WHERE ley_id = %s AND activa = true
            """, (ley_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Ley {ley_id} no encontrada o inactiva")
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))


def get_titulos_db(ley_id: int) -> list[dict]:
    """Devuelve la lista de títulos de una ley."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT titulo_id, numero, denominacion
                FROM normas.titulos
                WHERE ley_id = %s
                ORDER BY orden
            """, (ley_id,))
            return [{"titulo_id": r[0], "numero": r[1], "denominacion": r[2]}
                    for r in cur.fetchall()]


def get_articulos_por_titulo(titulo_id: int) -> list[dict]:
    """Recupera todos los artículos de un título ordenados por posición."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT numero, tipo, contenido
                FROM normas.articulos
                WHERE titulo_id = %s AND tipo = 'articulo'
                ORDER BY orden_global
            """, (titulo_id,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_estructura_db(ley_id: int) -> dict:
    """
    Extrae metadatos estructurales de una ley directamente desde la BD.
    Devuelve conteos y listados de títulos, capítulos, secciones y artículos.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM normas.titulos WHERE ley_id = %s",
                (ley_id,))
            n_titulos = cur.fetchone()[0]

            cur.execute("""
                SELECT numero, denominacion FROM normas.titulos
                WHERE ley_id = %s ORDER BY orden
            """, (ley_id,))
            titulos = [{"numero": r[0], "nombre": r[1]} for r in cur.fetchall()]

            cur.execute("""
                SELECT COUNT(*) FROM normas.capitulos c
                JOIN normas.titulos t ON c.titulo_id = t.titulo_id
                WHERE t.ley_id = %s
            """, (ley_id,))
            n_capitulos = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*) FROM normas.secciones s
                JOIN normas.capitulos c ON s.capitulo_id = c.capitulo_id
                JOIN normas.titulos t   ON c.titulo_id   = t.titulo_id
                WHERE t.ley_id = %s
            """, (ley_id,))
            n_secciones = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*) FROM normas.articulos
                WHERE ley_id = %s AND tipo = 'articulo'
            """, (ley_id,))
            n_articulos = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*) FROM normas.articulos
                WHERE ley_id = %s AND tipo IN (
                    'disposicion_adicional', 'disposicion_transitoria',
                    'disposicion_derogatoria', 'disposicion_final'
                )
            """, (ley_id,))
            n_disposiciones = cur.fetchone()[0]

            cur.execute(
                "SELECT COUNT(*) FROM normas.articulos WHERE ley_id = %s",
                (ley_id,))
            n_total = cur.fetchone()[0]

        return {
            "n_titulos":       n_titulos,
            "titulos":         titulos,
            "n_capitulos":     n_capitulos,
            "n_secciones":     n_secciones,
            "n_articulos":     n_articulos,
            "n_disposiciones": n_disposiciones,
            "n_total":         n_total,
        }


def search_articles(vector: list[float], ley_id: int,
                    k: int = TOP_K_ARTICLES) -> list[dict]:
    """
    Devuelve los k artículos más cercanos al vector dado (similitud coseno),
    filtrados por ley.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    a.numero,
                    a.tipo,
                    a.contenido,
                    1 - (a.embedding <=> %s::vector) AS similitud
                FROM normas.articulos a
                WHERE a.ley_id = %s
                  AND a.embedding IS NOT NULL
                ORDER BY a.embedding <=> %s::vector
                LIMIT %s
            """, (vector, ley_id, vector, k))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
