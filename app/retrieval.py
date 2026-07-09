"""
Capa de recuperación semántica sobre normas.*:
  - embed_query: vector[1536] con caché en memoria
  - search_articles: k artículos más similares, filtrados por ley
  - get_estructura_db: metadatos estructurales de una ley
  - get_leyes_disponibles: catálogo de leyes activas
"""

import os
import random
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


def get_bloque_y_epigrafes(ley_id: int, oposicion_codigo: str = "GACE") -> tuple[str | None, list[dict]]:
    """
    Bloque y epígrafes (temario oficial) de una ley dentro de una oposición.
    No asume una oposición fija por código: `oposicion_codigo` es un parámetro,
    para que una oposición nueva funcione sin tocar código.
    Devuelve (None, []) si la ley no pertenece a esa oposición o no tiene bloque asignado.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ol.bloque
                FROM normas.oposicion_leyes ol
                JOIN normas.oposiciones o ON o.oposicion_id = ol.oposicion_id
                WHERE o.codigo = %s AND ol.ley_id = %s
            """, (oposicion_codigo, ley_id))
            row = cur.fetchone()
            if not row or not row[0]:
                return None, []
            bloque = row[0]
            cur.execute("""
                SELECT e.epigrafe_id, e.tema, e.titulo
                FROM normas.epigrafes e
                JOIN normas.oposiciones o ON o.oposicion_id = e.oposicion_id
                WHERE o.codigo = %s AND e.bloque = %s
                ORDER BY e.tema
            """, (oposicion_codigo, bloque))
            epigrafes = [{"epigrafe_id": r[0], "tema": r[1], "titulo": r[2]} for r in cur.fetchall()]
            return bloque, epigrafes


def get_leyes_disponibles(oposicion_id: int | None = None,
                          bloques: tuple[str, ...] | None = None,
                          excluir_test: bool = False) -> list[dict]:
    """
    Lista las leyes activas. Filtra por oposición y opcionalmente por bloques.
    excluir_test=True omite las leyes marcadas como documentos de referencia
    (no examinables), como GACE_NORM.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if oposicion_id is not None:
                filtro_ref = "AND ol.excluir_test = FALSE" if excluir_test else ""
                if bloques:
                    cur.execute(f"""
                        SELECT l.ley_id, l.codigo, l.nombre, l.nombre_corto,
                               ol.preguntas_simulacro, ol.orden, ol.bloque
                        FROM normas.leyes l
                        JOIN normas.oposicion_leyes ol
                             ON l.ley_id = ol.ley_id AND ol.oposicion_id = %s
                        WHERE l.activa = true AND ol.bloque = ANY(%s)
                        {filtro_ref}
                        ORDER BY ol.bloque, ol.orden, l.codigo
                    """, (oposicion_id, list(bloques)))
                else:
                    cur.execute(f"""
                        SELECT l.ley_id, l.codigo, l.nombre, l.nombre_corto,
                               ol.preguntas_simulacro, ol.orden, ol.bloque
                        FROM normas.leyes l
                        JOIN normas.oposicion_leyes ol
                             ON l.ley_id = ol.ley_id AND ol.oposicion_id = %s
                        WHERE l.activa = true
                        {filtro_ref}
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


def get_capitulos_db(titulo_id: int) -> list[dict]:
    """Devuelve la lista de capítulos de un título."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT capitulo_id, numero, denominacion
                FROM normas.capitulos
                WHERE titulo_id = %s
                ORDER BY orden
            """, (titulo_id,))
            return [{"capitulo_id": r[0], "numero": r[1], "denominacion": r[2]}
                    for r in cur.fetchall()]


def get_articulos_por_capitulo(capitulo_id: int) -> list[dict]:
    """Recupera todos los artículos de un capítulo ordenados por posición."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT numero, tipo, contenido
                FROM normas.articulos
                WHERE capitulo_id = %s AND tipo = 'articulo'
                ORDER BY orden_global
            """, (capitulo_id,))
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


def get_preguntas_sm2(user_id: str,
                      oposicion_id: int,
                      bloques: tuple[str, ...],
                      n: int = 10) -> list[dict]:
    """
    Selecciona hasta n preguntas para una sesión SM-2:
    primero las pendientes de revisión (proxima_revision <= hoy),
    luego preguntas nuevas (sin historial) hasta completar n.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pt.pregunta_id, pt.articulo, pt.pregunta,
                       pt.opcion_a, pt.opcion_b, pt.opcion_c, pt.opcion_d,
                       pt.correcta, pt.explicacion, l.codigo AS ley_codigo,
                       pu.proxima_revision, pu.total_vistas, pu.total_correctas
                FROM normas.progreso_usuario pu
                JOIN normas.preguntas_test pt  ON pt.pregunta_id  = pu.pregunta_id
                JOIN normas.leyes l            ON l.ley_id        = pt.ley_id
                JOIN normas.oposicion_leyes ol ON ol.ley_id       = l.ley_id
                                              AND ol.oposicion_id = %s
                WHERE pu.user_id            = %s
                  AND pu.proxima_revision  <= CURRENT_DATE
                  AND pt.revisada = TRUE
                  AND pt.activa   = TRUE
                  AND ol.bloque   = ANY(%s)
                ORDER BY pu.proxima_revision
                LIMIT %s
            """, (oposicion_id, user_id, list(bloques), n))
            cols = [d[0] for d in cur.description]
            pendientes = [dict(zip(cols, row)) for row in cur.fetchall()]

            restantes = n - len(pendientes)
            if restantes <= 0:
                return pendientes

            vistos_ids = [p["pregunta_id"] for p in pendientes] or [0]
            cur.execute("""
                SELECT pt.pregunta_id, pt.articulo, pt.pregunta,
                       pt.opcion_a, pt.opcion_b, pt.opcion_c, pt.opcion_d,
                       pt.correcta, pt.explicacion, l.codigo AS ley_codigo,
                       NULL::date AS proxima_revision,
                       0 AS total_vistas, 0 AS total_correctas
                FROM normas.preguntas_test pt
                JOIN normas.leyes l            ON l.ley_id        = pt.ley_id
                JOIN normas.oposicion_leyes ol ON ol.ley_id       = l.ley_id
                                              AND ol.oposicion_id = %s
                WHERE pt.revisada = TRUE
                  AND pt.activa   = TRUE
                  AND ol.bloque   = ANY(%s)
                  AND NOT EXISTS (
                      SELECT 1 FROM normas.progreso_usuario pu
                      WHERE pu.user_id = %s AND pu.pregunta_id = pt.pregunta_id
                  )
                  AND NOT (pt.pregunta_id = ANY(%s::int[]))
                ORDER BY RANDOM()
                LIMIT %s
            """, (oposicion_id, list(bloques), user_id, vistos_ids, restantes))
            cols = [d[0] for d in cur.description]
            nuevas = [dict(zip(cols, row)) for row in cur.fetchall()]

            return pendientes + nuevas


def update_progreso_sm2(user_id: str, pregunta_id: int, correcto: bool) -> None:
    """Aplica SM-2 y hace upsert en progreso_usuario."""
    q = 4 if correcto else 0
    correcto_int = 1 if correcto else 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT intervalo, repeticiones, facilidad
                FROM normas.progreso_usuario
                WHERE user_id = %s AND pregunta_id = %s
            """, (user_id, pregunta_id))
            row = cur.fetchone()
            intervalo, repeticiones, facilidad = row if row else (1, 0, 2.50)

            if q >= 3:
                if repeticiones == 0:
                    nuevo_intervalo = 1
                elif repeticiones == 1:
                    nuevo_intervalo = 6
                else:
                    nuevo_intervalo = round(intervalo * float(facilidad))
                repeticiones += 1
            else:
                nuevo_intervalo = 1
                repeticiones = 0

            nueva_facilidad = round(
                max(1.3, float(facilidad) + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)), 2)

            cur.execute("""
                INSERT INTO normas.progreso_usuario
                    (user_id, pregunta_id, intervalo, repeticiones, facilidad,
                     proxima_revision, total_vistas, total_correctas,
                     ultima_correcta, ultima_vez)
                VALUES (%s, %s, %s, %s, %s, CURRENT_DATE + %s, 1, %s, %s, NOW())
                ON CONFLICT (user_id, pregunta_id) DO UPDATE SET
                    intervalo        = %s,
                    repeticiones     = %s,
                    facilidad        = %s,
                    proxima_revision = CURRENT_DATE + %s,
                    total_vistas     = normas.progreso_usuario.total_vistas + 1,
                    total_correctas  = normas.progreso_usuario.total_correctas + %s,
                    ultima_correcta  = %s,
                    ultima_vez       = NOW()
            """, (
                user_id, pregunta_id,
                nuevo_intervalo, repeticiones, nueva_facilidad,
                nuevo_intervalo, correcto_int, correcto,
                nuevo_intervalo, repeticiones, nueva_facilidad,
                nuevo_intervalo, correcto_int, correcto,
            ))
            conn.commit()


def _fase_por_cobertura(cobertura: float) -> str:
    """Umbral de fase por % de épigrafes del bloque con al menos 1 pregunta vista."""
    if cobertura < 0.25:
        return "inicio"
    if cobertura < 0.60:
        return "aprendizaje"
    if cobertura < 0.90:
        return "consolidacion"
    return "preexamen"


def get_fase_alumno(user_id: str, oposicion_id: int, bloque: str) -> dict:
    """
    Calcula el estado vivo del alumno en un bloque (fase por cobertura de
    épigrafes, preguntas vistas/correctas, % acierto agregado, "estudiado")
    y lo persiste en normas.plan_estudio (UPSERT) para lectura rápida desde
    get_stats_alumno. No se recalcula fase por trigger: se llama tras cada
    tanda de preguntas (junto a update_progreso_sm2).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM normas.epigrafes
                WHERE oposicion_id = %s AND bloque = %s
            """, (oposicion_id, bloque))
            total_epigrafes = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(DISTINCT pt.epigrafe_id),
                       COALESCE(SUM(pu.total_vistas), 0),
                       COALESCE(SUM(pu.total_correctas), 0)
                FROM normas.progreso_usuario pu
                JOIN normas.preguntas_test pt ON pt.pregunta_id = pu.pregunta_id
                WHERE pu.user_id = %s
                  AND pt.epigrafe_id IN (
                      SELECT epigrafe_id FROM normas.epigrafes
                      WHERE oposicion_id = %s AND bloque = %s
                  )
            """, (user_id, oposicion_id, bloque))
            epigrafes_cubiertos, vistas, correctas = cur.fetchone()

            cobertura = (epigrafes_cubiertos / total_epigrafes) if total_epigrafes else 0.0
            fase = _fase_por_cobertura(cobertura)
            porcentaje = round(100 * correctas / vistas, 2) if vistas else 0.0
            estudiado = porcentaje >= 70.0

            cur.execute("""
                INSERT INTO normas.plan_estudio
                    (user_id, oposicion_id, bloque, fase, preguntas_vistas,
                     preguntas_correctas, porcentaje_acierto, estudiado, actualizado_en)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (user_id, oposicion_id, bloque) DO UPDATE SET
                    fase                = EXCLUDED.fase,
                    preguntas_vistas    = EXCLUDED.preguntas_vistas,
                    preguntas_correctas = EXCLUDED.preguntas_correctas,
                    porcentaje_acierto  = EXCLUDED.porcentaje_acierto,
                    estudiado           = EXCLUDED.estudiado,
                    actualizado_en      = NOW()
            """, (user_id, oposicion_id, bloque, fase, vistas, correctas, porcentaje, estudiado))
        conn.commit()

    return {
        "bloque": bloque,
        "fase": fase,
        "cobertura_pct": round(cobertura * 100, 1),
        "preguntas_vistas": vistas,
        "preguntas_correctas": correctas,
        "porcentaje_acierto": porcentaje,
        "estudiado": estudiado,
    }


def get_stats_alumno(user_id: str, oposicion_id: int) -> dict:
    """
    Datos para el panel de inicio del alumno:
      - bloques: progreso por bloque, leído de normas.plan_estudio (estado
        cacheado, actualizado por get_fase_alumno tras cada tanda)
      - proxima_accion: recomendación por regla simple (no IA) — el bloque
        no estudiado con menor % de acierto, o simulacro personal si todos
        están estudiados, o prueba de nivel si aún no hay datos
      - actividad_reciente: últimas preguntas respondidas (SM-2)
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT bloque, fase, preguntas_vistas, preguntas_correctas,
                       porcentaje_acierto, estudiado, actualizado_en
                FROM normas.plan_estudio
                WHERE user_id = %s AND oposicion_id = %s
                ORDER BY bloque
            """, (user_id, oposicion_id))
            cols = [d[0] for d in cur.description]
            bloques = [dict(zip(cols, row)) for row in cur.fetchall()]

            cur.execute("""
                SELECT p.pregunta_id, p.ultima_vez, p.ultima_correcta,
                       pt.ley_id, l.nombre AS ley_nombre
                FROM normas.progreso_usuario p
                JOIN normas.preguntas_test pt ON pt.pregunta_id = p.pregunta_id
                JOIN normas.leyes l           ON l.ley_id       = pt.ley_id
                WHERE p.user_id = %s
                ORDER BY p.ultima_vez DESC NULLS LAST
                LIMIT 10
            """, (user_id,))
            cols2 = [d[0] for d in cur.description]
            actividad_reciente = [dict(zip(cols2, row)) for row in cur.fetchall()]

    if not bloques:
        proxima_accion = {
            "tipo": "prueba_nivel",
            "motivo": "Aún no has hecho la prueba de nivel.",
        }
    else:
        pendientes = [b for b in bloques if not b["estudiado"]]
        if pendientes:
            objetivo = min(pendientes, key=lambda b: b["porcentaje_acierto"])
            proxima_accion = {
                "tipo": "practicar_bloque",
                "bloque": objetivo["bloque"],
                "motivo": (
                    f"Bloque {objetivo['bloque']} con {objetivo['porcentaje_acierto']}% "
                    f"de acierto, aún no estudiado (≥70%)."
                ),
            }
        else:
            proxima_accion = {
                "tipo": "simulacro_personal",
                "motivo": "Todos los bloques están estudiados (≥70% de acierto).",
            }

    return {
        "bloques": bloques,
        "proxima_accion": proxima_accion,
        "actividad_reciente": actividad_reciente,
    }


# Porcentajes débiles/oficial/nueva por fase (diseño aprobado 05/07/2026)
FASES_MIX = {
    "inicio":        {"debiles": 0.00, "oficial": 0.40, "nueva": 0.60},
    "aprendizaje":   {"debiles": 0.15, "oficial": 0.20, "nueva": 0.65},
    "consolidacion": {"debiles": 0.30, "oficial": 0.25, "nueva": 0.45},
    "preexamen":     {"debiles": 0.40, "oficial": 0.35, "nueva": 0.25},
}

_COLUMNAS_PREGUNTA = """
    pt.pregunta_id, pt.articulo, pt.pregunta,
    pt.opcion_a, pt.opcion_b, pt.opcion_c, pt.opcion_d,
    pt.correcta, pt.explicacion, l.codigo AS ley_codigo
"""


def _fetch_debiles(cur, user_id, oposicion_id, bloque, limite):
    if limite <= 0:
        return []
    cur.execute(f"""
        SELECT {_COLUMNAS_PREGUNTA}
        FROM normas.progreso_usuario pu
        JOIN normas.preguntas_test pt ON pt.pregunta_id = pu.pregunta_id
        JOIN normas.leyes l            ON l.ley_id        = pt.ley_id
        JOIN normas.oposicion_leyes ol ON ol.ley_id       = l.ley_id
                                       AND ol.oposicion_id = %s
        WHERE pu.user_id = %s AND pu.ultima_correcta = FALSE
          AND ol.bloque = %s AND pt.revisada = TRUE AND pt.activa = TRUE
        ORDER BY RANDOM()
        LIMIT %s
    """, (oposicion_id, user_id, bloque, limite))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetch_por_fuente(cur, oposicion_id, bloque, fuente_filtro, excluir_ids, limite):
    if limite <= 0:
        return []
    excluir_ids = excluir_ids or [0]
    cur.execute(f"""
        SELECT {_COLUMNAS_PREGUNTA}
        FROM normas.preguntas_test pt
        JOIN normas.leyes l            ON l.ley_id        = pt.ley_id
        JOIN normas.oposicion_leyes ol ON ol.ley_id       = l.ley_id
                                       AND ol.oposicion_id = %s
        WHERE ol.bloque = %s AND pt.revisada = TRUE AND pt.activa = TRUE
          AND ({fuente_filtro})
          AND NOT (pt.pregunta_id = ANY(%s::int[]))
        ORDER BY RANDOM()
        LIMIT %s
    """, (oposicion_id, bloque, excluir_ids, limite))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_preguntas_adaptativo(user_id: str, oposicion_id: int, bloque: str, n: int = 10) -> list[dict]:
    """
    Tanda de práctica mezclando débiles/oficial/nueva según la fase actual
    del alumno en ese bloque (normas.plan_estudio; 'inicio' si aún no hay
    estado). Prioridad: se completa primero el % de débiles (preguntas con
    ultima_correcta=FALSE, cualquier fuente); el resto se reparte
    proporcionalmente entre oficial (fuente oficial_*) y nueva (fuente='ia'),
    excluyendo las ya elegidas. Si un tramo no tiene suficientes preguntas,
    el hueco se rellena con el resto para no devolver una tanda incompleta.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT fase FROM normas.plan_estudio
                WHERE user_id = %s AND oposicion_id = %s AND bloque = %s
            """, (user_id, oposicion_id, bloque))
            row = cur.fetchone()
            fase = row[0] if row else "inicio"
            mix = FASES_MIX[fase]

            n_debiles = round(n * mix["debiles"])
            debiles = _fetch_debiles(cur, user_id, oposicion_id, bloque, n_debiles)

            restantes = n - len(debiles)
            total_pct_resto = mix["oficial"] + mix["nueva"]
            n_oficial = round(restantes * mix["oficial"] / total_pct_resto) if total_pct_resto > 0 else 0
            n_nueva = restantes - n_oficial

            excluir = [p["pregunta_id"] for p in debiles]
            oficial = _fetch_por_fuente(
                cur, oposicion_id, bloque, "pt.fuente LIKE 'oficial_%%'", excluir, n_oficial
            )
            excluir += [p["pregunta_id"] for p in oficial]
            nueva = _fetch_por_fuente(
                cur, oposicion_id, bloque, "pt.fuente = 'ia'", excluir, n_nueva
            )

            faltan = n - len(debiles) - len(oficial) - len(nueva)
            if faltan > 0:
                excluir += [p["pregunta_id"] for p in nueva]
                relleno = _fetch_por_fuente(
                    cur, oposicion_id, bloque,
                    "pt.fuente LIKE 'oficial_%%' OR pt.fuente = 'ia'", excluir, faltan
                )
                nueva += relleno

    tanda = debiles + oficial + nueva
    random.shuffle(tanda)
    return tanda


def get_preguntas_simulacro_personal(user_id: str, oposicion_id: int, n: int = 50) -> dict:
    """
    Simulacro personal: n preguntas repartidas proporcionalmente (según el
    peso oficial oposicion_leyes.preguntas_simulacro) entre los bloques ya
    "estudiado" (>=70% acierto agregado) del alumno. Requiere que el alumno
    tenga plan_estudio en todos los bloques de la oposición (proxy de
    "prueba de nivel ya hecha"); si no, o si no tiene ningún bloque
    estudiado, devuelve disponible=False con el motivo.

    La fórmula oficial de corrección (A-(E/3)) se aplica al calificar las
    respuestas del alumno, no aquí — esta función solo selecciona preguntas.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT bloque FROM normas.oposicion_leyes
                WHERE oposicion_id = %s AND bloque IS NOT NULL
            """, (oposicion_id,))
            bloques_oposicion = {r[0] for r in cur.fetchall()}

            cur.execute("""
                SELECT bloque, estudiado FROM normas.plan_estudio
                WHERE user_id = %s AND oposicion_id = %s
            """, (user_id, oposicion_id))
            plan = {r[0]: r[1] for r in cur.fetchall()}

            if not bloques_oposicion.issubset(plan.keys()):
                return {
                    "disponible": False,
                    "motivo": "Debes completar la prueba de nivel (todos los bloques) antes del simulacro personal.",
                    "preguntas": [],
                }

            bloques_estudiados = sorted(b for b, ok in plan.items() if ok)
            if not bloques_estudiados:
                return {
                    "disponible": False,
                    "motivo": "Aún no tienes ningún bloque estudiado (≥70% de acierto agregado).",
                    "preguntas": [],
                }

            cur.execute("""
                SELECT bloque, SUM(preguntas_simulacro) AS peso
                FROM normas.oposicion_leyes
                WHERE oposicion_id = %s AND bloque = ANY(%s)
                GROUP BY bloque
            """, (oposicion_id, bloques_estudiados))
            pesos = {r[0]: r[1] for r in cur.fetchall()}
            total_peso = sum(pesos.values())

            reparto, asignadas = {}, 0
            for i, b in enumerate(bloques_estudiados):
                if i == len(bloques_estudiados) - 1:
                    cantidad = n - asignadas  # el último bloque absorbe el redondeo
                else:
                    cantidad = round(n * pesos[b] / total_peso)
                reparto[b] = cantidad
                asignadas += cantidad

            preguntas = []
            for b, cantidad in reparto.items():
                if cantidad <= 0:
                    continue
                cur.execute(f"""
                    SELECT {_COLUMNAS_PREGUNTA}
                    FROM normas.preguntas_test pt
                    JOIN normas.leyes l            ON l.ley_id        = pt.ley_id
                    JOIN normas.oposicion_leyes ol ON ol.ley_id       = l.ley_id
                                                   AND ol.oposicion_id = %s
                    WHERE ol.bloque = %s AND pt.revisada = TRUE AND pt.activa = TRUE
                    ORDER BY RANDOM()
                    LIMIT %s
                """, (oposicion_id, b, cantidad))
                cols = [d[0] for d in cur.description]
                preguntas += [dict(zip(cols, row)) for row in cur.fetchall()]

    random.shuffle(preguntas)
    return {"disponible": True, "motivo": None, "preguntas": preguntas}


def get_preguntas_prueba_nivel(oposicion_id: int, n: int = 40) -> list[dict]:
    """
    Prueba de nivel: n preguntas repartidas proporcionalmente por el peso
    oficial (oposicion_leyes.preguntas_simulacro) entre TODOS los bloques de
    la oposición — a diferencia del simulacro personal, no exige bloques
    "estudiado" (es la primera prueba del alumno, plan_estudio aún vacío).
    Ordenadas por dificultad creciente (fácil → difícil) para calibrar el
    nivel progresivamente. Nota: hoy casi todas las preguntas tienen
    dificultad=2 (default, pendiente de reclasificación — ver TODO.md), así
    que el efecto práctico del orden es limitado hasta reclasificar el banco.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT bloque, SUM(preguntas_simulacro) AS peso
                FROM normas.oposicion_leyes
                WHERE oposicion_id = %s AND bloque IS NOT NULL
                GROUP BY bloque
            """, (oposicion_id,))
            pesos = {r[0]: r[1] for r in cur.fetchall()}
            total_peso = sum(pesos.values())

            bloques = sorted(pesos)
            reparto, asignadas = {}, 0
            for i, b in enumerate(bloques):
                if i == len(bloques) - 1:
                    cantidad = n - asignadas  # el último bloque absorbe el redondeo
                else:
                    cantidad = round(n * pesos[b] / total_peso)
                reparto[b] = cantidad
                asignadas += cantidad

            preguntas = []
            for b, cantidad in reparto.items():
                if cantidad <= 0:
                    continue
                cur.execute(f"""
                    SELECT {_COLUMNAS_PREGUNTA}, pt.dificultad
                    FROM normas.preguntas_test pt
                    JOIN normas.leyes l            ON l.ley_id        = pt.ley_id
                    JOIN normas.oposicion_leyes ol ON ol.ley_id       = l.ley_id
                                                   AND ol.oposicion_id = %s
                    WHERE ol.bloque = %s AND pt.revisada = TRUE AND pt.activa = TRUE
                    ORDER BY pt.dificultad ASC, RANDOM()
                    LIMIT %s
                """, (oposicion_id, b, cantidad))
                cols = [d[0] for d in cur.description]
                preguntas += [dict(zip(cols, row)) for row in cur.fetchall()]

    preguntas.sort(key=lambda p: p["dificultad"])
    return preguntas


def get_preguntas_simulacro_academia(simulacro_id: int) -> dict:
    """
    Simulacro de academia: lee la lista ya fijada y ordenada en
    normas.simulacro_academia_preguntas (mismo simulacro para todos los
    alumnos). No genera ni personaliza nada — solo sirve lo ya autorizado.
    Devuelve disponible=False si el simulacro no existe o no está
    autorizado todavía (estado='generado', pendiente de que la academia
    lo apruebe).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT nombre, estado, fecha_inicio, fecha_fin
                FROM normas.simulacros_academia
                WHERE simulacro_id = %s
            """, (simulacro_id,))
            row = cur.fetchone()
            if not row:
                return {"disponible": False, "motivo": "Simulacro no encontrado.", "preguntas": []}

            nombre, estado, fecha_inicio, fecha_fin = row
            if estado != "autorizado":
                return {
                    "disponible": False,
                    "motivo": "Este simulacro aún no ha sido autorizado por la academia.",
                    "preguntas": [],
                }

            cur.execute(f"""
                SELECT {_COLUMNAS_PREGUNTA}, sap.orden
                FROM normas.simulacro_academia_preguntas sap
                JOIN normas.preguntas_test pt ON pt.pregunta_id = sap.pregunta_id
                JOIN normas.leyes l           ON l.ley_id       = pt.ley_id
                WHERE sap.simulacro_id = %s
                ORDER BY sap.orden
            """, (simulacro_id,))
            cols = [d[0] for d in cur.description]
            preguntas = [dict(zip(cols, row)) for row in cur.fetchall()]

    return {
        "disponible": True,
        "motivo": None,
        "nombre": nombre,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "preguntas": preguntas,
    }


def calificar_simulacro(oposicion_id: int, aciertos: int, errores: int, blancos: int,
                        n_preguntas: int) -> dict:
    """
    Aplica la fórmula oficial de la convocatoria vigente (año más reciente)
    a un resultado de simulacro ya cerrado, extrapolando aciertos/errores/
    blancos de n_preguntas al num_preguntas oficial para que la nota quede
    en la escala real (comparable a nota_minima/pct_aprobado). No persiste
    nada: solo calcula.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT num_preguntas, valor_acierto, penalizacion_error,
                       penalizacion_blanco, escala_min, escala_max, nota_minima
                FROM normas.convocatorias
                WHERE oposicion_id = %s
                ORDER BY año DESC
                LIMIT 1
            """, (oposicion_id,))
            row = cur.fetchone()

    if row is None:
        return {"disponible": False, "motivo": "No hay convocatoria configurada para esta oposición."}

    (num_oficial, valor_acierto, pen_error, pen_blanco,
     escala_min, escala_max, nota_minima) = row

    factor = num_oficial / n_preguntas
    a_ext, e_ext, b_ext = aciertos * factor, errores * factor, blancos * factor
    nota = a_ext * float(valor_acierto) - e_ext * float(pen_error) - b_ext * float(pen_blanco)
    nota = max(float(escala_min), min(float(escala_max), nota))

    return {
        "disponible": True,
        "nota": round(nota, 2),
        "escala_max": float(escala_max),
        "nota_minima": float(nota_minima),
        "aprobado": nota >= float(nota_minima),
        "aciertos": aciertos, "errores": errores, "blancos": blancos,
    }


def guardar_resultado_simulacro(user_id: str, oposicion_id: int, tipo: str, n_preguntas: int,
                                aciertos: int, errores: int, blancos: int, nota: float,
                                aprobado: bool, simulacro_academia_id: int | None = None) -> None:
    """Inserta un intento cerrado de simulacro en normas.historial_simulacros."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO normas.historial_simulacros
                    (user_id, oposicion_id, tipo, simulacro_academia_id, n_preguntas,
                     aciertos, errores, blancos, nota, aprobado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, oposicion_id, tipo, simulacro_academia_id, n_preguntas,
                  aciertos, errores, blancos, nota, aprobado))
        conn.commit()


def get_historial_simulacros(user_id: str, oposicion_id: int) -> list[dict]:
    """
    Historial de intentos de simulacro del alumno (personal y academia),
    para la sección "Mi progreso". Ordenado del más reciente al más antiguo.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tipo, n_preguntas, aciertos, errores, blancos, nota,
                       aprobado, realizado_en
                FROM normas.historial_simulacros
                WHERE user_id = %s AND oposicion_id = %s
                ORDER BY realizado_en DESC
            """, (user_id, oposicion_id))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
