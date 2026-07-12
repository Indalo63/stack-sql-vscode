-- ============================================================
-- Migración 039: descarte de preguntas (borrado lógico + justificación)
--
-- Motivo (auditoría de seguridad, 12/07/2026): el botón "Rechazar" del modo
-- Revisar hacía un DELETE real. Cualquier editor podía destruir trabajo de forma
-- irreversible, sin papelera y sin dejar rastro de quién lo borró ni por qué
-- (sí quedaba rastro de quién APROBABA: revisado_por / revisado_en).
--
-- A partir de ahora "Rechazar" no borra: marca la pregunta como descartada,
-- exige una justificación escrita y guarda quién y cuándo. Un administrador
-- puede consultarlas y restaurarlas.
--
-- No se reutiliza la columna `activa`: esa significa otra cosa ("pregunta ya
-- aprobada que se retira por incorrecta o duplicada"). Mezclar ambos estados
-- haría imposible distinguir "rechazada en revisión" de "retirada del banco".
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

ALTER TABLE normas.preguntas_test
    ADD COLUMN IF NOT EXISTS descartada      BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS motivo_descarte TEXT,
    ADD COLUMN IF NOT EXISTS descartada_por  VARCHAR(150),
    ADD COLUMN IF NOT EXISTS descartada_en   TIMESTAMP;

COMMENT ON COLUMN normas.preguntas_test.descartada IS
    'TRUE = rechazada en la revisión (borrado lógico). No aparece en la lista de pendientes ni llega a los alumnos. Un administrador puede restaurarla.';
COMMENT ON COLUMN normas.preguntas_test.motivo_descarte IS
    'Justificación escrita por el editor al rechazar. Obligatoria: sin motivo no se puede descartar.';
COMMENT ON COLUMN normas.preguntas_test.descartada_por IS
    'Email del editor que la rechazó.';
COMMENT ON COLUMN normas.preguntas_test.descartada_en IS
    'Fecha y hora del rechazo.';

-- Una pregunta descartada tiene siempre motivo, autor y fecha (coherencia de datos)
ALTER TABLE normas.preguntas_test
    DROP CONSTRAINT IF EXISTS preguntas_descarte_check;
ALTER TABLE normas.preguntas_test
    ADD CONSTRAINT preguntas_descarte_check CHECK (
        NOT descartada
        OR (motivo_descarte IS NOT NULL
            AND btrim(motivo_descarte) <> ''
            AND descartada_por IS NOT NULL
            AND descartada_en  IS NOT NULL)
    );

CREATE INDEX IF NOT EXISTS idx_preguntas_descartada
    ON normas.preguntas_test (descartada)
    WHERE descartada;

-- ── Verificación ──
SELECT COUNT(*) FILTER (WHERE descartada) AS descartadas,
       COUNT(*)                            AS total
FROM normas.preguntas_test;
