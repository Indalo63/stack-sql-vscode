-- Consultas sobre la Constitución Española (1978)
-- Base: esquema legislacion en stack_db
-- Objetivo: exploración del contenido y generación de preguntas Q&A
--
-- Secciones:
--   1. Navegación jerárquica
--   2. Consultas de contenido para Q&A
--   3. Búsqueda por palabra clave
--   4. Plantillas para generación de preguntas
--   5. Búsqueda semántica con pgvector (requiere embeddings generados)

-- =============================================================================
-- 1. NAVEGACIÓN JERÁRQUICA
-- =============================================================================

-- Todos los títulos con número de artículos
SELECT t.numero, t.denominacion, COUNT(a.articulo_id) AS articulos
FROM legislacion.titulos t
LEFT JOIN legislacion.articulos a ON a.titulo_id = t.titulo_id AND a.tipo = 'articulo'
WHERE t.ley_id = 1
GROUP BY t.titulo_id, t.numero, t.denominacion
ORDER BY t.orden;

-- Estructura completa: título > capítulo > sección > artículos
SELECT
    t.numero                          AS titulo,
    COALESCE(c.numero, '—')           AS capitulo,
    COALESCE(s.numero, '—')           AS seccion,
    COUNT(a.articulo_id)              AS articulos
FROM legislacion.articulos a
JOIN legislacion.titulos t ON a.titulo_id = t.titulo_id
LEFT JOIN legislacion.capitulos c ON a.capitulo_id = c.capitulo_id
LEFT JOIN legislacion.secciones s ON a.seccion_id = s.seccion_id
WHERE a.tipo = 'articulo'
GROUP BY t.orden, t.numero, c.orden, c.numero, s.orden, s.numero
ORDER BY t.orden, c.orden NULLS FIRST, s.orden NULLS FIRST;


-- =============================================================================
-- 2. CONSULTAS DE CONTENIDO PARA Q&A
-- =============================================================================

-- Texto de un artículo concreto
SELECT numero, contenido
FROM legislacion.articulos
WHERE tipo = 'articulo' AND numero = '14';

-- Todos los artículos de un título (para generar preguntas por bloque temático)
SELECT a.numero, a.contenido
FROM legislacion.articulos a
JOIN legislacion.titulos t ON a.titulo_id = t.titulo_id
WHERE t.numero = 'I' AND a.tipo = 'articulo'
ORDER BY a.orden_global;

-- Artículos de una sección concreta (derechos fundamentales)
SELECT a.numero, a.contenido
FROM legislacion.articulos a
JOIN legislacion.secciones s ON a.seccion_id = s.seccion_id
JOIN legislacion.capitulos c ON s.capitulo_id = c.capitulo_id
JOIN legislacion.titulos t ON c.titulo_id = t.titulo_id
WHERE t.numero = 'I' AND c.numero = 'SEGUNDO' AND s.numero = '1.ª'
ORDER BY a.orden_global;

-- Preámbulo
SELECT contenido
FROM legislacion.articulos
WHERE tipo = 'preambulo';

-- Todas las disposiciones (adicionales, transitorias, derogatoria, final)
SELECT numero, tipo, contenido
FROM legislacion.articulos
WHERE tipo != 'articulo' AND tipo != 'preambulo'
ORDER BY orden_global;


-- =============================================================================
-- 3. BÚSQUEDA POR PALABRA CLAVE (para localizar artículos relevantes)
-- =============================================================================

-- Artículos que contienen una palabra clave
SELECT numero, tipo,
       LEFT(contenido, 200) AS extracto
FROM legislacion.articulos
WHERE contenido ILIKE '%libertad%'
  AND tipo = 'articulo'
ORDER BY numero::int;

-- Buscar en qué artículo aparece un concepto jurídico
SELECT a.numero, t.numero AS titulo, LEFT(a.contenido, 150) AS extracto
FROM legislacion.articulos a
JOIN legislacion.titulos t ON a.titulo_id = t.titulo_id
WHERE a.contenido ILIKE '%Tribunal Constitucional%'
  AND a.tipo = 'articulo'
ORDER BY a.orden_global;


-- =============================================================================
-- 4. PLANTILLAS PARA GENERACIÓN AUTOMÁTICA DE PREGUNTAS
-- =============================================================================

-- Extraer artículos cortos (buenos para preguntas directas)
SELECT numero, contenido,
       LENGTH(contenido) AS longitud
FROM legislacion.articulos
WHERE tipo = 'articulo'
  AND LENGTH(contenido) < 300
ORDER BY LENGTH(contenido);

-- Artículos con apartados numerados (1., 2., 3. — útiles para preguntas de detalle)
SELECT numero,
       LEFT(contenido, 250) AS inicio
FROM legislacion.articulos
WHERE tipo = 'articulo'
  AND contenido ~ '^\d+\.'
ORDER BY numero::int;

-- Lote de artículos para pasar al modelo de lenguaje (con contexto jerárquico completo)
SELECT
    a.numero                          AS articulo,
    t.numero || ' – ' || t.denominacion AS titulo,
    COALESCE(c.denominacion, '')      AS capitulo,
    COALESCE(s.denominacion, '')      AS seccion,
    a.contenido
FROM legislacion.articulos a
JOIN legislacion.titulos t ON a.titulo_id = t.titulo_id
LEFT JOIN legislacion.capitulos c ON a.capitulo_id = c.capitulo_id
LEFT JOIN legislacion.secciones s ON a.seccion_id = s.seccion_id
WHERE a.tipo = 'articulo'
ORDER BY a.orden_global;


-- =============================================================================
-- 5. BÚSQUEDA SEMÁNTICA CON PGVECTOR
-- Requiere embeddings generados con scripts/generate_embeddings.py
-- Modelo: text-embedding-3-small (OpenAI) → 1536 dimensiones
-- =============================================================================

-- Estado de embeddings generados
SELECT
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) AS con_embedding,
    COUNT(*) FILTER (WHERE embedding IS NULL)     AS sin_embedding,
    COUNT(*)                                       AS total
FROM legislacion.articulos;

-- Buscar artículos por similitud semántica (sustituir [VECTOR] por el embedding de la consulta)
-- Uso: pasar el vector generado por el modelo de lenguaje para la pregunta del usuario
SELECT
    a.numero,
    t.numero || ' – ' || t.denominacion AS titulo,
    LEFT(a.contenido, 200)              AS extracto,
    1 - (a.embedding <=> '[VECTOR]')    AS similitud
FROM legislacion.articulos a
LEFT JOIN legislacion.titulos t ON a.titulo_id = t.titulo_id
WHERE a.embedding IS NOT NULL
ORDER BY a.embedding <=> '[VECTOR]'
LIMIT 5;

-- Top 3 artículos más relevantes para una pregunta (patrón para la app Q&A)
-- El vector de la pregunta se genera en la capa de aplicación y se pasa como parámetro
WITH pregunta AS (
    SELECT '[VECTOR]'::vector AS v
)
SELECT
    a.numero,
    a.tipo,
    LEFT(a.contenido, 300)           AS contenido,
    1 - (a.embedding <=> p.v)        AS similitud_coseno
FROM legislacion.articulos a, pregunta p
WHERE a.embedding IS NOT NULL
ORDER BY a.embedding <=> p.v
LIMIT 3;
