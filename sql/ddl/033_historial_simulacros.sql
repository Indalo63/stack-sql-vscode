-- ============================================================
-- Migración 033: tabla normas.historial_simulacros
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS normas.historial_simulacros (
    historial_id           BIGSERIAL     PRIMARY KEY,
    user_id                UUID          NOT NULL,
    oposicion_id           INTEGER       NOT NULL REFERENCES normas.oposiciones(oposicion_id) ON DELETE CASCADE,
    tipo                   VARCHAR(20)   NOT NULL CHECK (tipo IN ('personal', 'academia')),
    simulacro_academia_id  BIGINT        REFERENCES normas.simulacros_academia(simulacro_id) ON DELETE SET NULL,
    n_preguntas            INTEGER       NOT NULL,
    aciertos               INTEGER       NOT NULL,
    errores                INTEGER       NOT NULL,
    blancos                INTEGER       NOT NULL,
    nota                   NUMERIC(5,2)  NOT NULL,
    aprobado               BOOLEAN       NOT NULL,
    realizado_en           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CHECK (tipo <> 'academia' OR simulacro_academia_id IS NOT NULL)
);

COMMENT ON TABLE normas.historial_simulacros IS
    'Registro de cada intento de simulacro (personal o de academia) con su nota, para el informe general de progreso del alumno ("Mi progreso"). No afecta a progreso_usuario/plan_estudio: es histórico de examen completo, no de práctica adaptativa.';
COMMENT ON COLUMN normas.historial_simulacros.tipo IS
    'personal = simulacro individual del alumno (Paso 8, 50 preguntas). academia = simulacro con preguntas fijas de la academia (Paso 9), enlazado vía simulacro_academia_id.';
COMMENT ON COLUMN normas.historial_simulacros.nota IS
    'Nota ya extrapolada a la escala oficial de la convocatoria vigente (comparable a nota_minima/pct_aprobado), no la nota cruda sobre n_preguntas.';

CREATE INDEX IF NOT EXISTS idx_historial_simulacros_alumno
    ON normas.historial_simulacros (user_id, oposicion_id, realizado_en DESC);

-- Verificación
SELECT COUNT(*) AS total_historial FROM normas.historial_simulacros;
