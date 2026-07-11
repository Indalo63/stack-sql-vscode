-- ============================================================
-- Migración 034: normas.plan_estudio pasa a granularidad de tema (epígrafe)
-- Antes trackeaba progreso por bloque (I-VI); ahora por tema oficial (58
-- epígrafes GACE), para que el alumno pueda repasar un tema concreto en vez
-- de todo el bloque. El nivel de bloque ("estudiado", % acierto) se deriva
-- agregando sus temas en tiempo de lectura (retrieval.py), ya no se guarda
-- una fila propia por bloque.
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

ALTER TABLE normas.plan_estudio
    ADD COLUMN IF NOT EXISTS epigrafe_id INTEGER REFERENCES normas.epigrafes(epigrafe_id) ON DELETE CASCADE;

-- Las filas existentes son de la granularidad antigua (por bloque, sin
-- epigrafe_id) y quedan obsoletas: se regeneran solas la próxima vez que el
-- alumno practique (el progreso real vive en normas.progreso_usuario, no se
-- pierde nada — solo se recalcula el resumen agregado).
DELETE FROM normas.plan_estudio WHERE epigrafe_id IS NULL;

ALTER TABLE normas.plan_estudio
    ALTER COLUMN epigrafe_id SET NOT NULL;

ALTER TABLE normas.plan_estudio
    DROP CONSTRAINT IF EXISTS plan_estudio_user_id_oposicion_id_bloque_key;

ALTER TABLE normas.plan_estudio
    ADD CONSTRAINT plan_estudio_user_id_oposicion_id_epigrafe_id_key
    UNIQUE (user_id, oposicion_id, epigrafe_id);

COMMENT ON TABLE normas.plan_estudio IS
    'Estado vivo del alumno por tema oficial (epígrafe): fase del mix adaptativo, acierto agregado y si el tema está "estudiado" (≥70%). El nivel de bloque se deriva agregando sus temas en retrieval.py (get_stats_alumno) — ya no se guarda una fila propia por bloque. Se actualiza desde retrieval.py tras cada tanda, no desde triggers.';
COMMENT ON COLUMN normas.plan_estudio.bloque IS
    'Denormalizado desde normas.epigrafes.bloque para lecturas rápidas sin JOIN; se recalcula en cada UPSERT desde retrieval.get_fase_alumno.';
COMMENT ON COLUMN normas.plan_estudio.fase IS
    'Fase del mix adaptativo (inicio/aprendizaje/consolidacion/preexamen), calculada por número de preguntas vistas EN EL TEMA: inicio 0-4, aprendizaje 5-14, consolidacion 15-29, preexamen 30+.';
COMMENT ON COLUMN normas.plan_estudio.estudiado IS
    'TRUE cuando porcentaje_acierto >= 70 Y preguntas_vistas > 0 en este tema. Un bloque se considera "estudiado" cuando TODOS sus temas con preguntas vistas están en estudiado=TRUE (calculado en retrieval.py, no aquí).';

CREATE INDEX IF NOT EXISTS idx_plan_estudio_epigrafe
    ON normas.plan_estudio (epigrafe_id);

-- Verificación
SELECT COUNT(*) AS filas_plan_estudio FROM normas.plan_estudio;
SELECT COUNT(*) AS filas_sin_epigrafe FROM normas.plan_estudio WHERE epigrafe_id IS NULL;
