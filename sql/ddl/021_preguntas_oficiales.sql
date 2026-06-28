-- ============================================================
-- Migración 021: Soporte para preguntas oficiales GACE
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

-- ── 1. Hacer ley_id nullable (preguntas de leyes no cargadas en BD) ──────────
ALTER TABLE normas.preguntas_test
    ALTER COLUMN ley_id DROP NOT NULL;

-- ── 2. Añadir columna fuente ──────────────────────────────────────────────────
ALTER TABLE normas.preguntas_test
    ADD COLUMN IF NOT EXISTS fuente VARCHAR(20) NOT NULL DEFAULT 'ia'
        CHECK (fuente IN ('ia', 'oficial_2024', 'oficial_2025'));

-- ── 3. Añadir columna convocatoria ────────────────────────────────────────────
ALTER TABLE normas.preguntas_test
    ADD COLUMN IF NOT EXISTS convocatoria VARCHAR(4)
        CHECK (convocatoria IN ('2024', '2025'));

-- ── 4. Añadir columna para número de pregunta en examen oficial ───────────────
ALTER TABLE normas.preguntas_test
    ADD COLUMN IF NOT EXISTS num_pregunta_oficial INTEGER;

-- ── 5. Índices nuevos ─────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_preguntas_fuente
    ON normas.preguntas_test (fuente);
CREATE INDEX IF NOT EXISTS idx_preguntas_convocatoria
    ON normas.preguntas_test (convocatoria);

-- ── 6. Verificación ──────────────────────────────────────────────────────────
SELECT
    fuente,
    convocatoria,
    COUNT(*) AS total,
    COUNT(CASE WHEN revisada THEN 1 END) AS revisadas
FROM normas.preguntas_test
GROUP BY fuente, convocatoria
ORDER BY fuente, convocatoria;
