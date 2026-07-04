"""
Capa de recuperación semántica sobre normas.*:
  - embed_query: vector[1536] con caché en memoria
  - search_articles: k artículos más similares, filtrados por ley
  - get_estructura_db: metadatos estructurales de una ley
  - get_leyes_disponibles: catálogo de leyes activas
"""

import os
from openai import OpenAI
from app.config import OPENAI_EMBEDDING_MODEL, TOP_K_ARTICLES, SIMILARITY_THRESHOLD, OPENAI_API_KEY
from app.db import get_connection

_embedding_cache: dict[str, list[float]] = {}


def embed_query(text: str) -> list[float]:
    if text not in _embedding_cache:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=text)
        _embedding_cache[text] = response.data[0].embedding
    return _embedding_cache[text]


def get_oposiciones() -> list[dict]:
    """Devuelve las oposiciones activas."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT oposicion_id, codigo, nombre, nombre_corto
                FROM normas.oposiciones
                WHERE activa = true
                ORDER BY nombre_corto
            """)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_preguntas_banco(oposicion_id: int,
                        bloques: tuple[str, ...],
                        n: int = 10,
                        excluir_ids: tuple[int, ...] = ()) -> list[dict]:
    """N preguntas aleatorias aprobadas, filtradas por oposición + bloques."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pt.pregunta_id, pt.articulo, pt.pregunta,
                       pt.opcion_a, pt.opcion_b, pt.opcion_c, pt.opcion_d,
                       pt.correcta, pt.explicacion, l.codigo AS ley_codigo
                FROM normas.preguntas_test pt
                JOIN normas.leyes l            ON l.ley_id        = pt.ley_id
                JOIN normas.oposicion_leyes ol ON ol.ley_id       = l.ley_id
                                              AND ol.oposicion_id = %s
                WHERE pt.revisada = TRUE
                  AND pt.activa   = TRUE
                  AND ol.bloque   = ANY(%s)
                  AND NOT (pt.pregunta_id = ANY(%s::int[]))
                ORDER BY RANDOM()
                LIMIT %s
            """, (oposicion_id, list(bloques), list(excluir_ids), n))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_bloques_por_oposicion(oposicion_id: int) -> list[str]:
    """Devuelve los bloques distintos de una oposición, ordenados."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT bloque
                FROM normas.oposicion_leyes
                WHERE oposicion_id = %s AND bloque IS NOT NULL
                ORDER BY bloque
            """, (oposicion_id,))
            return [row[0] for row in cur.fetchall()]


def get_leyes_disponibles(oposicion_id: int | None = None,
                          bloques: tuple[str, ...] | None = None) -> list[dict]:
    """Lista las leyes activas. Filtra por oposición y opcionalmente por bloques."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if oposicion_id is not None:
                if bloques:
                    cur.execute("""
                        SELECT l.ley_id, l.codigo, l.nombre, l.nombre_corto,
                               ol.preguntas_simulacro, ol.orden, ol.bloque
                        FROM normas.leyes l
                        JOIN normas.oposicion_leyes ol
                             ON l.ley_id = ol.ley_id AND ol.oposicion_id = %s
                        WHERE l.activa = true AND ol.bloque = ANY(%s)
                        ORDER BY ol.bloque, ol.orden, l.codigo
                    """, (oposicion_id, list(bloques)))
                else:
                    cur.execute("""
                        SELECT l.ley_id, l.codigo, l.nombre, l.nombre_corto,
                               ol.preguntas_simulacro, ol.orden, ol.bloque
                        FROM normas.leyes l
                        JOIN normas.oposicion_leyes ol
                             ON l.ley_id = ol.ley_id AND ol.oposicion_id = %s
                        WHERE l.activa = true
                        ORDER BY ol.bloque, ol.orden, l.codigo
                    """, (oposicion_id,))
            else:
                cur.execute("""
                    SELECT ley_id, codigo, nombre, nombre_corto,
                           NULL AS preguntas_simulacro, NULL AS orden, NULL AS bloque
                    FROM normas.leyes
                    WHERE activa = true
                    ORDER BY nombre
                """)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_ley_info(ley_id: int) -> dict:
    """Devuelve metadatos de una ley (nombre, tipo, token_count, etc.)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ley_id, codigo, nombre, nombre_corto, tipo, token_count
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
                    k: int = TOP_K_ARTICLES,
                    min_similarity: float = 0.0) -> list[dict]:
    """
    Devuelve los k artículos más cercanos al vector dado (similitud coseno),
    filtrados por ley y umbral mínimo de similitud.
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
                  AND 1 - (a.embedding <=> %s::vector) >= %s
                ORDER BY a.embedding <=> %s::vector
                LIMIT %s
            """, (vector, ley_id, vector, min_similarity, vector, k))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def search_articles_hierarchical(vector: list[float], ley_id: int,
                                  k: int = TOP_K_ARTICLES,
                                  top_titulos: int = 3,
                                  min_similarity: float = 0.0) -> list[dict]:
    """
    Búsqueda en dos niveles para leyes grandes:
    1. Encuentra los `top_titulos` títulos más relevantes usando sus embeddings.
    2. Busca los k artículos más similares dentro de esos títulos.
    Fallback a búsqueda plana si los títulos no tienen embeddings.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Paso 1: títulos más relevantes
            cur.execute("""
                SELECT titulo_id
                FROM normas.titulos
                WHERE ley_id = %s AND embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (ley_id, vector, top_titulos))
            titulo_ids = [r[0] for r in cur.fetchall()]

            if not titulo_ids:
                return search_articles(vector, ley_id, k, min_similarity)

            # Paso 2: artículos dentro de los títulos seleccionados
            cur.execute("""
                SELECT
                    a.numero,
                    a.tipo,
                    a.contenido,
                    1 - (a.embedding <=> %s::vector) AS similitud
                FROM normas.articulos a
                WHERE a.titulo_id = ANY(%s)
                  AND a.embedding IS NOT NULL
                  AND 1 - (a.embedding <=> %s::vector) >= %s
                ORDER BY a.embedding <=> %s::vector
                LIMIT %s
            """, (vector, titulo_ids, vector, min_similarity, vector, k))
            cols = [d[0] for d in cur.description]
            resultados = [dict(zip(cols, row)) for row in cur.fetchall()]

            # Si el filtro por título devuelve poco, complementar con búsqueda plana
            if len(resultados) < k // 2:
                extra = search_articles(vector, ley_id, k, min_similarity)
                vistos = {r["numero"] for r in resultados}
                for e in extra:
                    if e["numero"] not in vistos:
                        resultados.append(e)
                resultados = sorted(resultados, key=lambda x: -x["similitud"])[:k]

            return resultados
