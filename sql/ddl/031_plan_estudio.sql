-- ============================================================
-- Migración 031: tabla normas.plan_estudio (estado vivo del alumno por bloque)
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS normas.plan_estudio (
    plan_id             BIGSERIAL    PRIMARY KEY,
    user_id             TEXT         NOT NULL,
    oposicion_id        INTEGER      NOT NULL REFERENCES normas.oposiciones(oposicion_id) ON DELETE CASCADE,
    bloque              VARCHAR(5)   NOT NULL,
    fase                VARCHAR(20)  NOT NULL DEFAULT 'inicio'
                        CHECK (fase IN ('inicio', 'aprendizaje', 'consolidacion', 'preexamen')),
    preguntas_vistas    INTEGER      NOT NULL DEFAULT 0,
    preguntas_correctas INTEGER      NOT NULL DEFAULT 0,
    porcentaje_acierto  NUMERIC(5,2) NOT NULL DEFAULT 0,
    estudiado           BOOLEAN      NOT NULL DEFAULT FALSE,
    actualizado_en      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    creado_en           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    UNIQUE (user_id, oposicion_id, bloque)
);

COMMENT ON TABLE normas.plan_estudio IS
    'Estado vivo del alumno por bloque: fase del mix adaptativo, acierto agregado y si el bloque está "estudiado" (≥70%). Se actualiza desde retrieval.py tras cada tanda, no desde triggers.';
COMMENT ON COLUMN normas.plan_estudio.fase IS
    'Fase del mix adaptativo (inicio/aprendizaje/consolidacion/preexamen). Umbral de transición por preguntas vistas AÚN NO DEFINIDO — de momento el valor se queda en "inicio" hasta implementar la lógica de transición en el Paso 5.';
COMMENT ON COLUMN normas.plan_estudio.estudiado IS
    'TRUE cuando porcentaje_acierto >= 70 (regla ya definida en el diseño aprobado).';

CREATE INDEX IF NOT EXISTS idx_plan_estudio_user
    ON normas.plan_estudio (user_id, oposicion_id);

-- Verificación
SELECT COUNT(*) AS filas_plan_estudio FROM normas.plan_estudio;
