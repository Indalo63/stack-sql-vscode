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


def es_editor_autorizado(email: str) -> bool:
    """
    ¿Esta cuenta Google puede entrar en "Gestión banco de preguntas"?

    Una sesión Google válida NO basta: el email debe estar en normas.editores
    con activo=TRUE (lista blanca, migración 036). Sin esta comprobación,
    cualquier cuenta de Google que completase el OAuth tendría acceso completo
    de gestión, incluido borrar preguntas.
    """
    if not email:
        return False
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1 FROM normas.editores
                WHERE LOWER(email) = LOWER(%s) AND activo = TRUE
            """, (email,))
            return cur.fetchone() is not None


def get_editor(email: str) -> dict | None:
    """Ficha del editor (email, nombre, rol, activo) o None si no está autorizado."""
    if not email:
        return None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT email, nombre, rol, activo, academia, creado_en, creado_por
                FROM normas.editores
                WHERE LOWER(email) = LOWER(%s) AND activo = TRUE
            """, (email,))
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))


def listar_editores() -> list[dict]:
    """Todos los editores, activos y revocados, para la pantalla de gestión."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT email, nombre, rol, activo, academia, creado_en, creado_por
                FROM normas.editores
                ORDER BY activo DESC, rol, email
            """)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def alta_editor(email: str, nombre: str, rol: str, creado_por: str) -> str | None:
    """
    Da de alta un editor. Devuelve None si fue bien, o el motivo del error.

    Reactiva la fila si el email ya existía revocado (activo=FALSE), para no
    perder la trazabilidad histórica de sus revisiones.
    """
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return "Indica un email válido."
    if rol not in ("admin", "editor"):
        return "Rol no válido."

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT activo FROM normas.editores WHERE LOWER(email) = %s", (email,))
            row = cur.fetchone()
            if row and row[0]:
                return f"{email} ya está dado de alta."
            cur.execute("""
                INSERT INTO normas.editores (email, nombre, rol, activo, creado_por)
                VALUES (%s, %s, %s, TRUE, %s)
                ON CONFLICT (email) DO UPDATE
                    SET activo = TRUE, nombre = EXCLUDED.nombre, rol = EXCLUDED.rol
            """, (email, (nombre or "").strip() or None, rol, creado_por))
        conn.commit()
    return None


def _admins_activos(cur, excluyendo: str | None = None) -> int:
    sql = "SELECT COUNT(*) FROM normas.editores WHERE activo = TRUE AND rol = 'admin'"
    params: list = []
    if excluyendo:
        sql += " AND LOWER(email) <> LOWER(%s)"
        params.append(excluyendo)
    cur.execute(sql, params)
    return cur.fetchone()[0]


def revocar_editor(email: str, quien: str) -> str | None:
    """
    Revoca a un editor (activo=FALSE, sin borrar la fila: conserva el histórico
    de preguntas_test.revisado_por). Devuelve None si fue bien, o el motivo.

    Dos protecciones anti-bloqueo, aplicadas aquí (no solo en la UI) para que
    ninguna vía pueda dejar la app sin acceso de gestión:
      1. Nadie puede revocarse a sí mismo.
      2. No se puede dejar cero administradores activos.
    """
    if email.strip().lower() == (quien or "").strip().lower():
        return "No puedes revocar tu propia cuenta."

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT rol, activo FROM normas.editores WHERE LOWER(email) = LOWER(%s)",
                (email,),
            )
            row = cur.fetchone()
            if not row:
                return "Ese editor no existe."
            rol, activo = row
            if not activo:
                return "Ese editor ya estaba revocado."
            if rol == "admin" and _admins_activos(cur, excluyendo=email) == 0:
                return ("No puedes revocar al último administrador activo: "
                        "la app se quedaría sin nadie que pueda gestionarla.")

            cur.execute(
                "UPDATE normas.editores SET activo = FALSE WHERE LOWER(email) = LOWER(%s)",
                (email,),
            )
        conn.commit()
    return None


def cambiar_rol_editor(email: str, rol: str, quien: str) -> str | None:
    """Cambia el rol. Misma protección: no dejar cero admins activos."""
    if rol not in ("admin", "editor"):
        return "Rol no válido."

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT rol, activo FROM normas.editores WHERE LOWER(email) = LOWER(%s)",
                (email,),
            )
            row = cur.fetchone()
            if not row or not row[1]:
                return "Ese editor no existe o está revocado."
            if row[0] == rol:
                return None
            if row[0] == "admin" and rol == "editor" and _admins_activos(cur, excluyendo=email) == 0:
                return ("No puedes quitarte el rol de administrador al último admin activo: "
                        "la app se quedaría sin nadie que pueda gestionarla.")

            cur.execute(
                "UPDATE normas.editores SET rol = %s WHERE LOWER(email) = LOWER(%s)",
                (rol, email),
            )
        conn.commit()
    return None


def pendientes_por_bloque(oposicion_id: int) -> dict[str, int]:
    """
    Preguntas IA pendientes de revisión, contadas por bloque.

    Para que el editor vea DÓNDE está el trabajo sin ir probando bloques a
    ciegas: el contador global dice cuántas hay, esto dice en cuál están.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ol.bloque, COUNT(*)
                FROM normas.preguntas_test pt
                JOIN normas.oposicion_leyes ol ON ol.ley_id = pt.ley_id
                                              AND ol.oposicion_id = %s
                WHERE pt.fuente = 'ia'
                  AND pt.revisada = FALSE
                  AND ol.excluir_test = FALSE
                GROUP BY ol.bloque
            """, (oposicion_id,))
            return {b: n for b, n in cur.fetchall()}


def pendientes_por_tema(oposicion_id: int) -> dict[int, int]:
    """
    Preguntas IA pendientes por tema oficial (epígrafe).

    Cuenta lo que el editor VERÍA al elegir ese tema, es decir, las pendientes
    de las leyes asociadas al tema. Como una misma ley puede ser relevante para
    varios temas, la suma de todos los temas puede exceder el total del banco:
    no es un reparto, es "cuántas verás aquí".
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT el.epigrafe_id, COUNT(*)
                FROM normas.preguntas_test pt
                JOIN normas.epigrafe_leyes el  ON el.ley_id = pt.ley_id
                JOIN normas.oposicion_leyes ol ON ol.ley_id = pt.ley_id
                                              AND ol.oposicion_id = %s
                WHERE pt.fuente = 'ia'
                  AND pt.revisada = FALSE
                  AND ol.excluir_test = FALSE
                GROUP BY el.epigrafe_id
            """, (oposicion_id,))
            return {e: n for e, n in cur.fetchall()}


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


def get_temas_por_bloque(oposicion_id: int, bloque: str) -> list[dict]:
    """Temas oficiales (epígrafes) de un bloque, para que el alumno elija qué repasar."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT epigrafe_id, tema, titulo, orden
                FROM normas.epigrafes
                WHERE oposicion_id = %s AND bloque = %s
                ORDER BY orden
            """, (oposicion_id, bloque))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_temas_por_bloques(oposicion_id: int, bloques: tuple[str, ...]) -> list[dict]:
    """Temas oficiales (epígrafes) de varios bloques a la vez, para el sidebar de Administración."""
    if not bloques:
        return []
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT epigrafe_id, bloque, tema, titulo, orden
                FROM normas.epigrafes
                WHERE oposicion_id = %s AND bloque = ANY(%s)
                ORDER BY bloque, orden
            """, (oposicion_id, list(bloques)))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


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
                          excluir_test: bool = False,
                          temas: tuple[int, ...] | None = None) -> list[dict]:
    """
    Lista las leyes activas. Filtra por oposición y opcionalmente por bloques
    y por temas (epigrafe_id, vía normas.epigrafe_leyes — relación curada por
    scripts/asignar_epigrafe_leyes.py, no limitada al bloque del tema: una ley
    puede ser relevante para un tema archivado en otro bloque del programa).
    excluir_test=True omite las leyes marcadas como documentos de referencia
    (no examinables), como GACE_NORM.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if oposicion_id is not None:
                filtro_ref = "AND ol.excluir_test = FALSE" if excluir_test else ""
                if temas:
                    # El filtro por tema manda: una ley relevante para el tema
                    # puede estar archivada en otro bloque del programa (p. ej.
                    # LRJSP es del bloque IV pero es la ley correcta para el
                    # tema I.9 "sector público institucional"), así que NO se
                    # exige además ol.bloque = ANY(bloques) — eso descartaría
                    # justo los cruces entre bloques que epigrafe_leyes existe
                    # para capturar.
                    cur.execute(f"""
                        SELECT l.ley_id, l.codigo, l.nombre, l.nombre_corto, l.nombre_oficial,
                               ol.preguntas_simulacro, ol.orden, ol.bloque
                        FROM normas.leyes l
                        JOIN normas.oposicion_leyes ol
                             ON l.ley_id = ol.ley_id AND ol.oposicion_id = %(oposicion_id)s
                        WHERE l.activa = true
                          AND EXISTS (
                              SELECT 1 FROM normas.epigrafe_leyes el
                              WHERE el.ley_id = l.ley_id AND el.epigrafe_id = ANY(%(temas)s)
                          )
                        {filtro_ref}
                        ORDER BY ol.bloque, ol.orden, l.codigo
                    """, {"oposicion_id": oposicion_id, "temas": list(temas)})
                elif bloques:
                    cur.execute(f"""
                        SELECT l.ley_id, l.codigo, l.nombre, l.nombre_corto, l.nombre_oficial,
                               ol.preguntas_simulacro, ol.orden, ol.bloque
                        FROM normas.leyes l
                        JOIN normas.oposicion_leyes ol
                             ON l.ley_id = ol.ley_id AND ol.oposicion_id = %(oposicion_id)s
                        WHERE l.activa = true AND ol.bloque = ANY(%(bloques)s)
                        {filtro_ref}
                        ORDER BY ol.bloque, ol.orden, l.codigo
                    """, {"oposicion_id": oposicion_id, "bloques": list(bloques)})
                else:
                    cur.execute(f"""
                        SELECT l.ley_id, l.codigo, l.nombre, l.nombre_corto, l.nombre_oficial,
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
                    SELECT ley_id, codigo, nombre, nombre_corto, nombre_oficial,
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
                SELECT ley_id, codigo, nombre, nombre_corto, nombre_oficial, tipo, token_count
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
                      ley_ids: tuple[int, ...],
                      n: int = 10) -> list[dict]:
    """
    Selecciona hasta n preguntas para una sesión SM-2:
    primero las pendientes de revisión (proxima_revision <= hoy),
    luego preguntas nuevas (sin historial) hasta completar n.

    Recibe leyes concretas (no bloques): quien llama ya ha acotado el ámbito a
    un tema o a unas leyes dentro de un bloque, nunca al bloque entero.
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
                  AND pt.ley_id   = ANY(%s)
                ORDER BY pu.proxima_revision
                LIMIT %s
            """, (oposicion_id, user_id, list(ley_ids), n))
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
                  AND pt.ley_id   = ANY(%s)
                  AND NOT EXISTS (
                      SELECT 1 FROM normas.progreso_usuario pu
                      WHERE pu.user_id = %s AND pu.pregunta_id = pt.pregunta_id
                  )
                  AND NOT (pt.pregunta_id = ANY(%s::int[]))
                ORDER BY RANDOM()
                LIMIT %s
            """, (oposicion_id, list(ley_ids), user_id, vistos_ids, restantes))
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


def _fase_por_vistas(vistas: int) -> str:
    """Umbral de fase por número de preguntas vistas EN EL TEMA (diseño confirmado 11/07/2026)."""
    if vistas < 5:
        return "inicio"
    if vistas < 15:
        return "aprendizaje"
    if vistas < 30:
        return "consolidacion"
    return "preexamen"


def get_fase_alumno(user_id: str, oposicion_id: int, epigrafe_id: int) -> dict:
    """
    Calcula el estado vivo del alumno en un tema oficial (epígrafe): fase por
    preguntas vistas, preguntas vistas/correctas, % acierto agregado y si el
    tema está "estudiado" (≥70%). Lo persiste en normas.plan_estudio (UPSERT,
    una fila por tema) para lectura rápida desde get_stats_alumno. No se
    recalcula por trigger: se llama tras cada tanda de preguntas, una vez por
    cada tema tocado en esa tanda (junto a update_progreso_sm2).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT bloque FROM normas.epigrafes WHERE epigrafe_id = %s
            """, (epigrafe_id,))
            row = cur.fetchone()
            bloque = row[0] if row else None

            cur.execute("""
                SELECT COALESCE(SUM(pu.total_vistas), 0),
                       COALESCE(SUM(pu.total_correctas), 0)
                FROM normas.progreso_usuario pu
                JOIN normas.preguntas_test pt ON pt.pregunta_id = pu.pregunta_id
                WHERE pu.user_id = %s AND pt.epigrafe_id = %s
            """, (user_id, epigrafe_id))
            vistas, correctas = cur.fetchone()

            fase = _fase_por_vistas(vistas)
            porcentaje = round(100 * correctas / vistas, 2) if vistas else 0.0
            estudiado = vistas > 0 and porcentaje >= 70.0

            cur.execute("""
                INSERT INTO normas.plan_estudio
                    (user_id, oposicion_id, bloque, epigrafe_id, fase, preguntas_vistas,
                     preguntas_correctas, porcentaje_acierto, estudiado, actualizado_en)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (user_id, oposicion_id, epigrafe_id) DO UPDATE SET
                    bloque              = EXCLUDED.bloque,
                    fase                = EXCLUDED.fase,
                    preguntas_vistas    = EXCLUDED.preguntas_vistas,
                    preguntas_correctas = EXCLUDED.preguntas_correctas,
                    porcentaje_acierto  = EXCLUDED.porcentaje_acierto,
                    estudiado           = EXCLUDED.estudiado,
                    actualizado_en      = NOW()
            """, (user_id, oposicion_id, bloque, epigrafe_id, fase, vistas, correctas, porcentaje, estudiado))
        conn.commit()

    return {
        "epigrafe_id": epigrafe_id,
        "bloque": bloque,
        "fase": fase,
        "preguntas_vistas": vistas,
        "preguntas_correctas": correctas,
        "porcentaje_acierto": porcentaje,
        "estudiado": estudiado,
    }


def _fase_bloque(cur, user_id: str, oposicion_id: int, bloque: str) -> str:
    """Fase agregada del bloque completo (modo "Todo el bloque"): vistas medias por tema."""
    cur.execute("""
        SELECT COALESCE(AVG(COALESCE(pe.preguntas_vistas, 0)), 0)
        FROM normas.epigrafes e
        LEFT JOIN normas.plan_estudio pe
               ON pe.epigrafe_id = e.epigrafe_id AND pe.user_id = %s AND pe.oposicion_id = %s
        WHERE e.oposicion_id = %s AND e.bloque = %s
    """, (user_id, oposicion_id, oposicion_id, bloque))
    avg_vistas = cur.fetchone()[0]
    return _fase_por_vistas(round(float(avg_vistas)))


def get_stats_alumno(user_id: str, oposicion_id: int) -> dict:
    """
    Datos para el panel de inicio del alumno:
      - bloques: cada uno con su acierto agregado, si está "estudiado" (todos
        sus temas con preguntas vistas ≥70%) y el desglose de sus temas
        oficiales (normas.plan_estudio LEFT JOIN normas.epigrafes, así que
        aparecen también los temas aún sin practicar, con 0%).
      - proxima_accion: recomendación por regla simple (no IA) — el tema más
        débil ya practicado, o el primer tema sin practicar si no hay ninguno
        flojo, o simulacro personal si todo está estudiado, o prueba de nivel
        si aún no hay datos.
      - actividad_reciente: últimas preguntas respondidas (SM-2).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.bloque, e.epigrafe_id, e.tema, e.titulo, e.orden,
                       COALESCE(pe.fase, 'inicio'),
                       COALESCE(pe.preguntas_vistas, 0),
                       COALESCE(pe.preguntas_correctas, 0),
                       COALESCE(pe.porcentaje_acierto, 0),
                       COALESCE(pe.estudiado, FALSE)
                FROM normas.epigrafes e
                LEFT JOIN normas.plan_estudio pe
                       ON pe.epigrafe_id = e.epigrafe_id
                      AND pe.user_id = %s AND pe.oposicion_id = %s
                WHERE e.oposicion_id = %s
                ORDER BY e.orden
            """, (user_id, oposicion_id, oposicion_id))
            filas = cur.fetchall()

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

    por_bloque: dict[str, dict] = {}
    for bloque, epigrafe_id, tema, titulo, orden, fase, vistas, correctas, pct, estudiado in filas:
        b = por_bloque.setdefault(bloque, {
            "bloque": bloque, "temas": [], "preguntas_vistas": 0, "preguntas_correctas": 0,
        })
        b["temas"].append({
            "bloque": bloque, "epigrafe_id": epigrafe_id, "tema": tema, "titulo": titulo,
            "orden": orden, "fase": fase, "preguntas_vistas": vistas,
            "preguntas_correctas": correctas, "porcentaje_acierto": float(pct),
            "estudiado": estudiado,
        })
        b["preguntas_vistas"] += vistas
        b["preguntas_correctas"] += correctas

    bloques = []
    for b in por_bloque.values():
        temas_con_vistas = [t for t in b["temas"] if t["preguntas_vistas"] > 0]
        estudiado_bloque = bool(temas_con_vistas) and all(t["estudiado"] for t in temas_con_vistas)
        pct_bloque = (
            round(100 * b["preguntas_correctas"] / b["preguntas_vistas"], 2)
            if b["preguntas_vistas"] else 0.0
        )
        bloques.append({
            "bloque": b["bloque"], "temas": b["temas"],
            "preguntas_vistas": b["preguntas_vistas"], "preguntas_correctas": b["preguntas_correctas"],
            "porcentaje_acierto": pct_bloque, "estudiado": estudiado_bloque,
        })
    bloques.sort(key=lambda b: b["bloque"])

    if not filas:
        proxima_accion = {
            "tipo": "prueba_nivel",
            "motivo": "Aún no has hecho la prueba de nivel.",
        }
    else:
        todos_temas = [t for b in bloques for t in b["temas"]]
        debiles = [t for t in todos_temas if t["preguntas_vistas"] > 0 and not t["estudiado"]]
        if debiles:
            objetivo = min(debiles, key=lambda t: t["porcentaje_acierto"])
            proxima_accion = {
                "tipo": "practicar_tema",
                "bloque": objetivo["bloque"],
                "epigrafe_id": objetivo["epigrafe_id"],
                "motivo": (
                    f"Tema {objetivo['bloque']}.{objetivo['tema']} con "
                    f"{objetivo['porcentaje_acierto']}% de acierto, aún no estudiado (≥70%)."
                ),
            }
        else:
            sin_practicar = [t for t in todos_temas if t["preguntas_vistas"] == 0]
            if sin_practicar:
                objetivo = sin_practicar[0]
                proxima_accion = {
                    "tipo": "practicar_tema",
                    "bloque": objetivo["bloque"],
                    "epigrafe_id": objetivo["epigrafe_id"],
                    "motivo": f"Todavía no has practicado el tema {objetivo['bloque']}.{objetivo['tema']}.",
                }
            else:
                proxima_accion = {
                    "tipo": "simulacro_personal",
                    "motivo": "Todos los temas están estudiados (≥70% de acierto).",
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
    pt.correcta, pt.explicacion, l.codigo AS ley_codigo, pt.epigrafe_id
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
    Tanda de práctica sobre TODO el bloque, mezclando débiles/oficial/nueva
    según la fase agregada del bloque (media de preguntas vistas de sus
    temas — ver _fase_bloque; el progreso vivo ya no se guarda por bloque,
    solo por tema). Prioridad: se completa primero el % de débiles (preguntas
    con ultima_correcta=FALSE, cualquier fuente); el resto se reparte
    proporcionalmente entre oficial (fuente oficial_*) y nueva (fuente='ia'),
    excluyendo las ya elegidas. Si un tramo no tiene suficientes preguntas,
    el hueco se rellena con el resto para no devolver una tanda incompleta.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            fase = _fase_bloque(cur, user_id, oposicion_id, bloque)
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


def _fetch_debiles_tema(cur, user_id, epigrafe_id, limite):
    if limite <= 0:
        return []
    cur.execute(f"""
        SELECT {_COLUMNAS_PREGUNTA}
        FROM normas.progreso_usuario pu
        JOIN normas.preguntas_test pt ON pt.pregunta_id = pu.pregunta_id
        JOIN normas.leyes l           ON l.ley_id       = pt.ley_id
        WHERE pu.user_id = %s AND pu.ultima_correcta = FALSE
          AND pt.epigrafe_id = %s AND pt.revisada = TRUE AND pt.activa = TRUE
        ORDER BY RANDOM()
        LIMIT %s
    """, (user_id, epigrafe_id, limite))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetch_por_fuente_tema(cur, epigrafe_id, fuente_filtro, excluir_ids, limite):
    if limite <= 0:
        return []
    excluir_ids = excluir_ids or [0]
    cur.execute(f"""
        SELECT {_COLUMNAS_PREGUNTA}
        FROM normas.preguntas_test pt
        JOIN normas.leyes l ON l.ley_id = pt.ley_id
        WHERE pt.epigrafe_id = %s AND pt.revisada = TRUE AND pt.activa = TRUE
          AND ({fuente_filtro})
          AND NOT (pt.pregunta_id = ANY(%s::int[]))
        ORDER BY RANDOM()
        LIMIT %s
    """, (epigrafe_id, excluir_ids, limite))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_preguntas_adaptativo_tema(user_id: str, oposicion_id: int, epigrafe_id: int, n: int = 10) -> list[dict]:
    """
    Tanda de práctica acotada a UN tema oficial (epígrafe), mezclando
    débiles/oficial/nueva según la fase actual del alumno en ese tema
    (normas.plan_estudio; 'inicio' si aún no hay estado). Mismo criterio de
    reparto y relleno que get_preguntas_adaptativo, pero filtrando por
    epigrafe_id directamente en vez de por bloque completo.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT fase FROM normas.plan_estudio
                WHERE user_id = %s AND oposicion_id = %s AND epigrafe_id = %s
            """, (user_id, oposicion_id, epigrafe_id))
            row = cur.fetchone()
            fase = row[0] if row else "inicio"
            mix = FASES_MIX[fase]

            n_debiles = round(n * mix["debiles"])
            debiles = _fetch_debiles_tema(cur, user_id, epigrafe_id, n_debiles)

            restantes = n - len(debiles)
            total_pct_resto = mix["oficial"] + mix["nueva"]
            n_oficial = round(restantes * mix["oficial"] / total_pct_resto) if total_pct_resto > 0 else 0
            n_nueva = restantes - n_oficial

            excluir = [p["pregunta_id"] for p in debiles]
            oficial = _fetch_por_fuente_tema(
                cur, epigrafe_id, "pt.fuente LIKE 'oficial_%%'", excluir, n_oficial
            )
            excluir += [p["pregunta_id"] for p in oficial]
            nueva = _fetch_por_fuente_tema(
                cur, epigrafe_id, "pt.fuente = 'ia'", excluir, n_nueva
            )

            faltan = n - len(debiles) - len(oficial) - len(nueva)
            if faltan > 0:
                excluir += [p["pregunta_id"] for p in nueva]
                relleno = _fetch_por_fuente_tema(
                    cur, epigrafe_id,
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
    "estudiado" (todos sus temas con preguntas vistas ≥70%, ver
    get_stats_alumno) del alumno. Requiere que el alumno haya practicado al
    menos un tema en cada bloque de la oposición (proxy de "prueba de nivel
    ya hecha"); si no, o si no tiene ningún bloque estudiado, devuelve
    disponible=False con el motivo.

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

            stats = get_stats_alumno(user_id, oposicion_id)
            bloques_con_datos = {b["bloque"] for b in stats["bloques"] if b["preguntas_vistas"] > 0}

            if not bloques_oposicion.issubset(bloques_con_datos):
                return {
                    "disponible": False,
                    "motivo": "Debes completar la prueba de nivel (todos los bloques) antes del simulacro personal.",
                    "preguntas": [],
                }

            bloques_estudiados = sorted(b["bloque"] for b in stats["bloques"] if b["estudiado"])
            if not bloques_estudiados:
                return {
                    "disponible": False,
                    "motivo": "Aún no tienes ningún bloque estudiado (todos sus temas vistos con ≥70% de acierto).",
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


def generar_simulacro_academia(oposicion_id: int, nombre: str, n: int,
                               fecha_inicio, fecha_fin, academia: str | None = None) -> int:
    """
    Genera un simulacro de academia: reparto proporcional por peso oficial
    (oposicion_leyes.preguntas_simulacro) entre TODOS los bloques de la
    oposición — igual examen para todos los alumnos, sin personalización, a
    diferencia del simulacro personal que solo usa bloques "estudiado".
    Queda en estado 'generado'; hay que llamar a autorizar_simulacro_academia
    para que sea visible a los alumnos. Devuelve el simulacro_id creado.
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

            pregunta_ids = []
            for b, cantidad in reparto.items():
                if cantidad <= 0:
                    continue
                cur.execute("""
                    SELECT pt.pregunta_id
                    FROM normas.preguntas_test pt
                    JOIN normas.leyes l            ON l.ley_id        = pt.ley_id
                    JOIN normas.oposicion_leyes ol ON ol.ley_id       = l.ley_id
                                                   AND ol.oposicion_id = %s
                    WHERE ol.bloque = %s AND pt.revisada = TRUE AND pt.activa = TRUE
                    ORDER BY RANDOM()
                    LIMIT %s
                """, (oposicion_id, b, cantidad))
                pregunta_ids += [r[0] for r in cur.fetchall()]

            random.shuffle(pregunta_ids)

            cur.execute("""
                INSERT INTO normas.simulacros_academia
                    (academia, oposicion_id, nombre, fecha_inicio, fecha_fin)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING simulacro_id
            """, (academia, oposicion_id, nombre, fecha_inicio, fecha_fin))
            simulacro_id = cur.fetchone()[0]

            cur.executemany("""
                INSERT INTO normas.simulacro_academia_preguntas (simulacro_id, pregunta_id, orden)
                VALUES (%s, %s, %s)
            """, [(simulacro_id, pid, i) for i, pid in enumerate(pregunta_ids, 1)])
        conn.commit()

    return simulacro_id


def autorizar_simulacro_academia(simulacro_id: int, autorizado_por: str) -> None:
    """Marca un simulacro 'generado' como 'autorizado', fijando su selección de preguntas."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE normas.simulacros_academia
                SET estado = 'autorizado', autorizado_por = %s, autorizado_en = NOW()
                WHERE simulacro_id = %s AND estado = 'generado'
            """, (autorizado_por, simulacro_id))
        conn.commit()


def listar_simulacros_academia(oposicion_id: int) -> list[dict]:
    """Todos los simulacros de academia de una oposición, para el panel de Administración."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT sa.simulacro_id, sa.nombre, sa.estado, sa.fecha_inicio, sa.fecha_fin,
                       sa.autorizado_por, sa.autorizado_en, sa.generado_en,
                       COUNT(sap.pregunta_id) AS n_preguntas
                FROM normas.simulacros_academia sa
                LEFT JOIN normas.simulacro_academia_preguntas sap
                       ON sap.simulacro_id = sa.simulacro_id
                WHERE sa.oposicion_id = %s
                GROUP BY sa.simulacro_id
                ORDER BY sa.generado_en DESC
            """, (oposicion_id,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_simulacros_academia_disponibles(oposicion_id: int, user_id: str) -> list[dict]:
    """
    Simulacros de academia autorizados y dentro de su ventana temporal ahora
    mismo. Marca ya_realizado si el alumno ya tiene un intento guardado en
    historial_simulacros — solo se permite un intento por simulacro.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT sa.simulacro_id, sa.nombre, sa.fecha_inicio, sa.fecha_fin,
                       EXISTS (
                           SELECT 1 FROM normas.historial_simulacros hs
                           WHERE hs.simulacro_academia_id = sa.simulacro_id
                             AND hs.user_id = %s
                       ) AS ya_realizado
                FROM normas.simulacros_academia sa
                WHERE sa.oposicion_id = %s AND sa.estado = 'autorizado'
                  AND NOW() BETWEEN sa.fecha_inicio AND sa.fecha_fin
                ORDER BY sa.fecha_fin
            """, (user_id, oposicion_id))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


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
