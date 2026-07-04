-- ============================================================
-- Migración 027: Sistema de repaso adaptativo SM-2
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS normas.progreso_usuario (
    progreso_id      BIGSERIAL    PRIMARY KEY,
    user_id          TEXT         NOT NULL,
    pregunta_id      INTEGER      NOT NULL
                     REFERENCES normas.preguntas_test(pregunta_id) ON DELETE CASCADE,
    -- SM-2
    intervalo        INTEGER      NOT NULL DEFAULT 1,
    repeticiones     SMALLINT     NOT NULL DEFAULT 0,
    facilidad        NUMERIC(4,2) NOT NULL DEFAULT 2.50,
    proxima_revision DATE         NOT NULL DEFAULT CURRENT_DATE,
    -- Historial
    total_vistas     INTEGER      NOT NULL DEFAULT 0,
    total_correctas  INTEGER      NOT NULL DEFAULT 0,
    ultima_correcta  BOOLEAN,
    ultima_vez       TIMESTAMPTZ  DEFAULT NOW(),

    UNIQUE (user_id, pregunta_id)
);

-- Índice principal: preguntas pendientes de revisión por usuario
CREATE INDEX IF NOT EXISTS idx_progreso_user_fecha
    ON normas.progreso_usuario (user_id, proxima_revision);

-- Verificación
SELECT COUNT(*) AS registros FROM normas.progreso_usuario;
