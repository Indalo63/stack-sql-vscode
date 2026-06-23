-- Consultas sobre la Constitución Española (1978)
-- Base: schema normas en stack_db (ley_id = 1)
-- Objetivo: exploración del contenido y generación de preguntas Q&A
--
-- Secciones:
--   1. Navegación jerárquica
--   2. Consultas de contenido para Q&A
--   3. Búsqueda por palabra clave (full-text con tsvector)
--   4. Plantillas para generación de preguntas
--   5. Búsqueda semántica con pgvector

-- =============================================================================
-- 1. NAVEGACIÓN JERÁRQUICA
-- =============================================================================

-- Todos los títulos con número de artículos
SELECT t.numero, t.denominacion, COUNT(a.articulo_id) AS articulos
FROM normas.titulos t
LEFT JOIN normas.articulos a ON a.titulo_id = t.titulo_id AND a.tipo = 'articulo'
WHERE t.ley_id = 1
GROUP BY t.titulo_id, t.numero, t.denominacion
ORDER BY t.orden;

-- Estructura completa: título > capítulo > sección > artículos
SELECT
    t.numero                          AS titulo,
    COALESCE(c.numero, '—')           AS capitulo,
    COALESCE(s.numero, '—')           AS seccion,
    COUNT(a.articulo_id)              AS articulos
FROM normas.articulos a
JOIN normas.titulos t    ON a.titulo_id   = t.titulo_id
LEFT JOIN normas.capitulos c ON a.capitulo_id = c.capitulo_id
LEFT JOIN normas.secciones s ON a.seccion_id  = s.seccion_id
WHERE a.tipo = 'articulo' AND a.ley_id = 1
GROUP BY t.orden, t.numero, c.orden, c.numero, s.orden, s.numero
ORDER BY t.orden, c.orden NULLS FIRST, s.orden NULLS FIRST;


-- =============================================================================
-- 2. CONSULTAS DE CONTENIDO PARA Q&A
-- =============================================================================

-- Texto de un artículo concreto
SELECT numero, contenido
FROM normas.articulos
WHERE ley_id = 1 AND tipo = 'articulo' AND numero = '14';

-- Todos los artículos de un título
SELECT a.numero, a.contenido
FROM normas.articulos a
JOIN normas.titulos t ON a.titulo_id = t.titulo_id
WHERE t.ley_id = 1 AND t.numero = 'I' AND a.tipo = 'articulo'
ORDER BY a.orden_global;

-- Artículos de una sección concreta (derechos fundamentales)
SELECT a.numero, a.contenido
FROM normas.articulos a
JOIN normas.secciones s  ON a.seccion_id  = s.seccion_id
JOIN normas.capitulos c  ON s.capitulo_id = c.capitulo_id
JOIN normas.titulos t    ON c.titulo_id   = t.titulo_id
WHERE t.ley_id = 1 AND t.numero = 'I' AND c.numero = 'SEGUNDO' AND s.numero = '1.ª'
ORDER BY a.orden_global;

-- Preámbulo
SELECT contenido
FROM normas.articulos
WHERE ley_id = 1 AND tipo = 'preambulo';

-- Todas las disposiciones
SELECT numero, tipo, contenido
FROM normas.articulos
WHERE ley_id = 1
  AND tipo IN ('disposicion_adicional','disposicion_transitoria',
               'disposicion_derogatoria','disposicion_final')
ORDER BY orden_global;


-- =============================================================================
-- 3. BÚSQUEDA POR PALABRA CLAVE (full-text con índice GIN)
-- =============================================================================

-- Artículos que contienen una palabra clave (usando índice tsvector)
SELECT numero, tipo, ts_headline('spanish', contenido, query) AS extracto
FROM normas.articulos, to_tsquery('spanish', 'libertad') query
WHERE ley_id = 1 AND tipo = 'articulo'
  AND texto_buscable @@ query
ORDER BY ts_rank(texto_buscable, query) DESC;

-- Búsqueda ILIKE (sin índice, para exploración rápida)
SELECT a.numero, t.numero AS titulo, LEFT(a.contenido, 150) AS extracto
FROM normas.articulos a
JOIN normas.titulos t ON a.titulo_id = t.titulo_id
WHERE a.ley_id = 1
  AND a.contenido ILIKE '%Tribunal Constitucional%'
  AND a.tipo = 'articulo'
ORDER BY a.orden_global;


-- =============================================================================
-- 4. PLANTILLAS PARA GENERACIÓN AUTOMÁTICA DE PREGUNTAS
-- =============================================================================

-- Artículos cortos (buenos para preguntas directas)
SELECT numero, contenido, LENGTH(contenido) AS longitud
FROM normas.articulos
WHERE ley_id = 1 AND tipo = 'articulo' AND LENGTH(contenido) < 300
ORDER BY LENGTH(contenido);

-- Lote con contexto jerárquico completo (para pasar al LLM)
SELECT
    a.numero                              AS articulo,
    t.numero || ' – ' || t.denominacion  AS titulo,
    COALESCE(c.denominacion, '')          AS capitulo,
    COALESCE(s.denominacion, '')          AS seccion,
    a.contenido
FROM normas.articulos a
JOIN normas.titulos t    ON a.titulo_id   = t.titulo_id
LEFT JOIN normas.capitulos c ON a.capitulo_id = c.capitulo_id
LEFT JOIN normas.secciones s ON a.seccion_id  = s.seccion_id
WHERE a.ley_id = 1 AND a.tipo = 'articulo'
ORDER BY a.orden_global;


-- =============================================================================
-- 5. BÚSQUEDA SEMÁNTICA CON PGVECTOR
-- Modelo: text-embedding-3-small (OpenAI) — 1536 dimensiones
-- Índice HNSW con similitud coseno
-- =============================================================================

-- Estado de embeddings
SELECT
    l.codigo,
    COUNT(*) FILTER (WHERE a.embedding IS NOT NULL) AS con_embedding,
    COUNT(*) FILTER (WHERE a.embedding IS NULL)     AS sin_embedding,
    COUNT(*)                                         AS total
FROM normas.articulos a
JOIN normas.leyes l ON a.ley_id = l.ley_id
GROUP BY l.ley_id, l.codigo
ORDER BY l.codigo;

-- Buscar artículos por similitud semántica (sustituir [VECTOR] por el embedding de la consulta)
SELECT
    a.numero,
    t.numero || ' – ' || t.denominacion AS titulo,
    LEFT(a.contenido, 200)              AS extracto,
    1 - (a.embedding <=> '[VECTOR]')    AS similitud
FROM normas.articulos a
LEFT JOIN normas.titulos t ON a.titulo_id = t.titulo_id
WHERE a.ley_id = 1 AND a.embedding IS NOT NULL
ORDER BY a.embedding <=> '[VECTOR]'
LIMIT 5;
