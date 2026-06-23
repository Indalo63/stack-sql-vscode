-- ============================================================
-- Migración: legislacion.* → normas.*
-- Fuente: Constitución Española (CE1978)
-- 185 artículos con embeddings vector(1536)
--
-- Requisito previo: sql/ddl/010_schema_v2.sql ejecutado.
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- 1. LEY
-- ------------------------------------------------------------
INSERT INTO normas.leyes (
    codigo, nombre, nombre_corto, tipo, numero_oficial,
    fecha_pub, url_eli, activa
)
SELECT
    codigo,
    nombre,
    'CE'              AS nombre_corto,
    'constitucion'    AS tipo,
    'CE 1978'         AS numero_oficial,
    fecha_pub,
    url_eli,
    activa
FROM legislacion.leyes
WHERE codigo = 'CE1978';

-- Estima token_count desde longitud de texto (≈4 chars/token)
UPDATE normas.leyes
SET token_count = (
    SELECT SUM(LENGTH(contenido)) / 4
    FROM legislacion.articulos la
    JOIN legislacion.leyes ll ON la.ley_id = ll.ley_id
    WHERE ll.codigo = 'CE1978'
)
WHERE codigo = 'CE1978';

-- ------------------------------------------------------------
-- 2. TÍTULOS
-- (sin embeddings en el schema v1 — se generarán en el Paso 2)
-- ------------------------------------------------------------
INSERT INTO normas.titulos (ley_id, numero, denominacion, orden)
SELECT
    (SELECT ley_id FROM normas.leyes WHERE codigo = 'CE1978'),
    lt.numero,
    lt.denominacion,
    lt.orden
FROM legislacion.titulos lt
WHERE lt.ley_id = (SELECT ley_id FROM legislacion.leyes WHERE codigo = 'CE1978')
ORDER BY lt.orden;

-- ------------------------------------------------------------
-- 3. CAPÍTULOS
-- Join por (titulo.numero) para reasignar IDs correctamente
-- ------------------------------------------------------------
INSERT INTO normas.capitulos (titulo_id, numero, denominacion, orden)
SELECT
    nt.titulo_id,
    lc.numero,
    lc.denominacion,
    lc.orden
FROM legislacion.capitulos lc
JOIN legislacion.titulos lt  ON lc.titulo_id = lt.titulo_id
JOIN normas.titulos nt       ON nt.numero    = lt.numero
                             AND nt.ley_id   = (SELECT ley_id FROM normas.leyes WHERE codigo = 'CE1978')
ORDER BY nt.titulo_id, lc.orden;

-- ------------------------------------------------------------
-- 4. SECCIONES
-- Join en cadena: seccion → capitulo → titulo → nuevo IDs
-- ------------------------------------------------------------
INSERT INTO normas.secciones (capitulo_id, numero, denominacion, orden)
SELECT
    nc.capitulo_id,
    ls.numero,
    ls.denominacion,
    ls.orden
FROM legislacion.secciones ls
JOIN legislacion.capitulos lc ON ls.capitulo_id = lc.capitulo_id
JOIN legislacion.titulos lt   ON lc.titulo_id   = lt.titulo_id
JOIN normas.titulos nt        ON nt.numero       = lt.numero
                              AND nt.ley_id      = (SELECT ley_id FROM normas.leyes WHERE codigo = 'CE1978')
JOIN normas.capitulos nc      ON nc.titulo_id    = nt.titulo_id
                              AND nc.numero      = lc.numero
ORDER BY nc.capitulo_id, ls.orden;

-- ------------------------------------------------------------
-- 5. ARTÍCULOS (incluyendo embeddings vector(1536))
-- LEFT JOINs: algunos artículos no tienen capítulo o sección
-- ------------------------------------------------------------
INSERT INTO normas.articulos (
    ley_id, titulo_id, capitulo_id, seccion_id,
    numero, tipo, contenido, orden_global, embedding
)
SELECT
    (SELECT ley_id FROM normas.leyes WHERE codigo = 'CE1978'),
    nt.titulo_id,
    nc.capitulo_id,
    ns.seccion_id,
    la.numero,
    la.tipo,
    la.contenido,
    la.orden_global,
    la.embedding
FROM legislacion.articulos la
LEFT JOIN legislacion.titulos   lt ON la.titulo_id   = lt.titulo_id
LEFT JOIN legislacion.capitulos lc ON la.capitulo_id = lc.capitulo_id
LEFT JOIN legislacion.secciones ls ON la.seccion_id  = ls.seccion_id
LEFT JOIN normas.titulos nt
       ON nt.numero  = lt.numero
      AND nt.ley_id  = (SELECT ley_id FROM normas.leyes WHERE codigo = 'CE1978')
LEFT JOIN normas.capitulos nc
       ON nc.titulo_id = nt.titulo_id
      AND nc.numero    = lc.numero
LEFT JOIN normas.secciones ns
       ON ns.capitulo_id = nc.capitulo_id
      AND ns.numero      = ls.numero
WHERE la.ley_id = (SELECT ley_id FROM legislacion.leyes WHERE codigo = 'CE1978')
ORDER BY la.orden_global;

-- ------------------------------------------------------------
-- VERIFICACIÓN
-- ------------------------------------------------------------
DO $$
DECLARE
    v_src_titulos    int;
    v_src_capitulos  int;
    v_src_secciones  int;
    v_src_articulos  int;
    v_src_embeddings int;

    v_dst_titulos    int;
    v_dst_capitulos  int;
    v_dst_secciones  int;
    v_dst_articulos  int;
    v_dst_embeddings int;
BEGIN
    SELECT COUNT(*) INTO v_src_titulos    FROM legislacion.titulos;
    SELECT COUNT(*) INTO v_src_capitulos  FROM legislacion.capitulos;
    SELECT COUNT(*) INTO v_src_secciones  FROM legislacion.secciones;
    SELECT COUNT(*) INTO v_src_articulos  FROM legislacion.articulos;
    SELECT COUNT(*) INTO v_src_embeddings FROM legislacion.articulos WHERE embedding IS NOT NULL;

    SELECT COUNT(*) INTO v_dst_titulos    FROM normas.titulos;
    SELECT COUNT(*) INTO v_dst_capitulos  FROM normas.capitulos;
    SELECT COUNT(*) INTO v_dst_secciones  FROM normas.secciones;
    SELECT COUNT(*) INTO v_dst_articulos  FROM normas.articulos;
    SELECT COUNT(*) INTO v_dst_embeddings FROM normas.articulos WHERE embedding IS NOT NULL;

    RAISE NOTICE '--- Verificación migración CE1978 ---';
    RAISE NOTICE 'Títulos:    origen=% destino=% %', v_src_titulos,   v_dst_titulos,   CASE WHEN v_src_titulos   = v_dst_titulos   THEN 'OK' ELSE 'ERROR' END;
    RAISE NOTICE 'Capítulos:  origen=% destino=% %', v_src_capitulos, v_dst_capitulos, CASE WHEN v_src_capitulos = v_dst_capitulos THEN 'OK' ELSE 'ERROR' END;
    RAISE NOTICE 'Secciones:  origen=% destino=% %', v_src_secciones, v_dst_secciones, CASE WHEN v_src_secciones = v_dst_secciones THEN 'OK' ELSE 'ERROR' END;
    RAISE NOTICE 'Artículos:  origen=% destino=% %', v_src_articulos, v_dst_articulos, CASE WHEN v_src_articulos = v_dst_articulos THEN 'OK' ELSE 'ERROR' END;
    RAISE NOTICE 'Embeddings: origen=% destino=% %', v_src_embeddings, v_dst_embeddings, CASE WHEN v_src_embeddings = v_dst_embeddings THEN 'OK' ELSE 'ERROR' END;

    IF v_src_titulos   != v_dst_titulos   OR
       v_src_capitulos != v_dst_capitulos OR
       v_src_secciones != v_dst_secciones OR
       v_src_articulos != v_dst_articulos OR
       v_src_embeddings != v_dst_embeddings
    THEN
        RAISE EXCEPTION 'Migración incompleta — revisando conteos arriba';
    END IF;

    RAISE NOTICE '--------------------------------------';
    RAISE NOTICE 'Migración completada correctamente.';
END $$;

COMMIT;
