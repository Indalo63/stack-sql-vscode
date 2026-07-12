-- ============================================================
-- Migración 041: marca de datos de prueba del MVP
--
-- CONTEXTO (leer antes de tocar nada):
-- Para validar el motor de aprendizaje con 2 alumnos de prueba hace falta un
-- banco mínimo. Pero aprobar preguntas SIN revisión humana **degrada la lógica
-- de negocio**: el banco revisado es el producto, y lo que nos distingue de la
-- competencia es precisamente que un humano lo valida.
--
-- Solución: todo lo que se apruebe sin revisión real queda marcado con
-- `es_prueba = TRUE`. Así:
--   1. Se distingue SIEMPRE del banco de verdad (las 209 oficiales revisadas).
--   2. Se puede revertir a "pendiente de revisión" con un solo comando, sin
--      tocar nada más (scripts/limpiar_datos_prueba.py).
--   3. Si algún día se olvida limpiar, la marca sigue ahí y se ve.
--
-- ⚠️ NADA con es_prueba = TRUE debe llegar a un alumno real de pago.
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

ALTER TABLE normas.preguntas_test
    ADD COLUMN IF NOT EXISTS es_prueba BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN normas.preguntas_test.es_prueba IS
    'TRUE = pregunta aprobada SIN revisión humana real, solo para validar el motor con los alumnos de prueba del MVP. NO forma parte del banco de calidad. Reversible con scripts/limpiar_datos_prueba.py. Nunca debe llegar a un alumno de pago.';

CREATE INDEX IF NOT EXISTS idx_preguntas_es_prueba
    ON normas.preguntas_test (es_prueba) WHERE es_prueba;

-- ── Verificación ──
-- Cuántas preguntas son de prueba y cuántas son banco real
SELECT es_prueba,
       COUNT(*) FILTER (WHERE revisada)     AS aprobadas,
       COUNT(*) FILTER (WHERE NOT revisada) AS pendientes,
       COUNT(*)                             AS total
FROM normas.preguntas_test
GROUP BY es_prueba
ORDER BY es_prueba;
