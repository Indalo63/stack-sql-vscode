-- ============================================================
-- Migración 024: Auditoría de revisión en banco de preguntas
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

-- ── 1. Añadir columnas de auditoría ──────────────────────────────────────────
ALTER TABLE normas.preguntas_test
    ADD COLUMN IF NOT EXISTS revisado_por VARCHAR(150),  -- email Google del revisor
    ADD COLUMN IF NOT EXISTS revisado_en  TIMESTAMP;     -- fecha y hora de la revisión

COMMENT ON COLUMN normas.preguntas_test.revisado_por IS
    'Email Google del editor/revisor que aprobó la pregunta.';
COMMENT ON COLUMN normas.preguntas_test.revisado_en IS
    'Fecha y hora en que se marcó revisada=TRUE.';

-- ── 2. Índice para consultas por revisor ──────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_preguntas_revisado_por
    ON normas.preguntas_test (revisado_por)
    WHERE revisado_por IS NOT NULL;

-- ── 3. Verificación ──────────────────────────────────────────────────────────
SELECT
    fuente,
    COUNT(*)                                          AS total,
    COUNT(CASE WHEN revisada     THEN 1 END)          AS revisadas,
    COUNT(CASE WHEN revisado_por IS NOT NULL THEN 1 END) AS con_revisor
FROM normas.preguntas_test
GROUP BY fuente
ORDER BY fuente;
