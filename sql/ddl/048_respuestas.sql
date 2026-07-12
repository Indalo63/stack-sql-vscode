-- ============================================================
-- Migración 048: registro de respuestas (QUÉ opción eligió el alumno)
--
-- EL PROBLEMA
-- `progreso_usuario` solo guardaba `ultima_correcta` (sí/no) y los contadores
-- agregados. **Se estaba tirando la señal pedagógica más valiosa que existe:
-- QUÉ distractor eligió el alumno cuando falló.**
--
-- Sin ese dato es IMPOSIBLE:
--   · Analizar los distractores (¿cuál engaña? ¿cuál no lo elige nadie?).
--   · Calcular el índice de DISCRIMINACIÓN del ítem, que detecta automáticamente
--     preguntas rotas, ambiguas o con la respuesta MAL MARCADA.
--   · Diagnosticar el error de verdad ("confundes los plazos", no "fallaste").
--   · Entrenar la decisión de dejar en blanco (la fórmula A−E/3 penaliza fallar,
--     así que responder a ciegas RESTA: saber cuándo callar es una destreza).
--
-- Y lo más importante: **los datos que no se guardan hoy no se recuperan mañana.**
-- Cada respuesta que un alumno da sin registrar es información perdida para
-- siempre.
--
-- POR QUÉ UNA TABLA NUEVA Y NO UNA COLUMNA
-- `progreso_usuario` tiene UNA fila por (alumno, pregunta): guarda el ESTADO
-- actual del SM-2, no el historial. Aquí hace falta lo contrario: una fila por
-- CADA respuesta, para poder analizar la evolución y agregar por ítem.
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS normas.respuestas (
    respuesta_id    BIGSERIAL PRIMARY KEY,
    user_id         TEXT        NOT NULL,      -- UUID de Supabase Auth
    pregunta_id     INTEGER     NOT NULL REFERENCES normas.preguntas_test(pregunta_id) ON DELETE CASCADE,
    opcion_elegida  CHAR(1),                   -- 'a'|'b'|'c'|'d'  ·  NULL = EN BLANCO
    correcta        BOOLEAN     NOT NULL,      -- FALSE también si la dejó en blanco
    contexto        VARCHAR(24) NOT NULL,      -- de dónde salió la respuesta
    segundos        INTEGER,                   -- tiempo empleado (para el cronómetro; hoy NULL)
    respondido_en   TIMESTAMP   NOT NULL DEFAULT NOW(),

    CONSTRAINT respuestas_opcion_check
        CHECK (opcion_elegida IS NULL OR opcion_elegida IN ('a','b','c','d')),
    CONSTRAINT respuestas_contexto_check
        CHECK (contexto IN ('repaso','prueba_nivel','simulacro_personal',
                            'simulacro_academia','practica_editor')),
    -- Una respuesta en blanco nunca puede ser correcta
    CONSTRAINT respuestas_blanco_check
        CHECK (opcion_elegida IS NOT NULL OR correcta = FALSE)
);

COMMENT ON TABLE normas.respuestas IS
    'Una fila por CADA respuesta de un alumno. Guarda QUÉ opción eligió (o NULL si la dejó en blanco), que es el dato que permite el análisis de distractores, el índice de discriminación del ítem (detector de preguntas rotas o mal marcadas) y el diagnóstico real del error. progreso_usuario guarda el ESTADO del SM-2; esto guarda el HISTORIAL.';
COMMENT ON COLUMN normas.respuestas.opcion_elegida IS
    'La opción que marcó. NULL = la dejó EN BLANCO. Importa: con la fórmula A−E/3, dejar en blanco es una decisión estratégica, no una no-respuesta.';
COMMENT ON COLUMN normas.respuestas.contexto IS
    'De dónde salió la respuesta. Importa para el análisis: en un simulacro (con penalización y reloj) el alumno responde distinto que en un repaso.';
COMMENT ON COLUMN normas.respuestas.segundos IS
    'Tiempo empleado. Hoy NULL: se rellenará cuando se implemente el cronómetro (54 s/pregunta en el examen real).';

CREATE INDEX IF NOT EXISTS idx_respuestas_pregunta ON normas.respuestas (pregunta_id);
CREATE INDEX IF NOT EXISTS idx_respuestas_usuario  ON normas.respuestas (user_id, respondido_en DESC);

-- ── Verificación ──
SELECT contexto, COUNT(*) AS respuestas,
       COUNT(*) FILTER (WHERE opcion_elegida IS NULL) AS en_blanco
FROM normas.respuestas GROUP BY contexto ORDER BY contexto;
