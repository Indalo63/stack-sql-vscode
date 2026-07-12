-- ============================================================
-- Migración 049: discriminación del ítem (detector de preguntas defectuosas)
--
-- QUÉ ES Y POR QUÉ IMPORTA
-- La dificultad (migración 047) es solo LA MITAD de la teoría clásica de test.
-- La otra mitad es la **discriminación**: ¿esta pregunta distingue al que sabe
-- del que no sabe?
--
--   · Discriminación ALTA  -> los que dominan la materia la aciertan; los que no,
--     la fallan. Es una buena pregunta.
--   · Discriminación NULA  -> la aciertan (o fallan) todos por igual. No aporta
--     información: no mide nada.
--   · Discriminación NEGATIVA -> **los BUENOS la fallan MÁS que los malos**.
--     Eso es una señal de alarma: casi siempre significa que la pregunta está
--     ROTA — enunciado ambiguo, dos opciones defendibles, o **la respuesta
--     marcada MAL** (el error más grave y más difícil de ver a ojo).
--
-- Es decir: **un detector AUTOMÁTICO de preguntas defectuosas en el banco**.
-- Ningún editor puede revisar 1.800 preguntas a mano buscando claves mal
-- marcadas; esto las señala solo. Y el control de calidad del banco es
-- exactamente lo que se le vende a una academia (B2B).
--
-- CÓMO SE CALCULA
-- Correlación biserial-puntual entre acertar el ítem (1/0) y la **capacidad
-- general** del alumno (su % de acierto en todo lo demás). Se usa la capacidad
-- CORREGIDA (excluyendo el propio ítem): si no, la pregunta se correlaciona
-- consigo misma e infla el resultado.
--
-- ⚠️ NECESITA ESCALA. Con 2 alumnos esto no dice nada. Madura con decenas de
-- alumnos (una academia). Por eso el umbral vive en BD.
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

ALTER TABLE normas.preguntas_test
    ADD COLUMN IF NOT EXISTS discriminacion   NUMERIC(5,3),   -- -1.000 .. 1.000
    ADD COLUMN IF NOT EXISTS discriminacion_n INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS alerta_calidad   VARCHAR(24);

ALTER TABLE normas.preguntas_test
    DROP CONSTRAINT IF EXISTS preguntas_alerta_check;
ALTER TABLE normas.preguntas_test
    ADD CONSTRAINT preguntas_alerta_check CHECK (
        alerta_calidad IS NULL OR alerta_calidad IN
            ('clave_sospechosa', 'no_discrimina', 'distractor_muerto')
    );

COMMENT ON COLUMN normas.preguntas_test.discriminacion IS
    'Correlación biserial-puntual entre acertar esta pregunta y la capacidad general del alumno. NEGATIVA = los buenos la fallan más que los malos = pregunta rota (ambigua o con la clave mal marcada). NULL = aún sin datos suficientes.';
COMMENT ON COLUMN normas.preguntas_test.discriminacion_n IS
    'Respuestas sobre las que se calculó. Con pocas, el número es ruido.';
COMMENT ON COLUMN normas.preguntas_test.alerta_calidad IS
    'clave_sospechosa = discriminación negativa o un distractor elegido más que la correcta -> revisar YA. no_discrimina = no distingue a nadie. distractor_muerto = alguna opción no la elige nadie (la pregunta es de 3 opciones en la práctica).';

CREATE INDEX IF NOT EXISTS idx_preguntas_alerta
    ON normas.preguntas_test (alerta_calidad) WHERE alerta_calidad IS NOT NULL;

-- Umbral de respuestas para fiarse de la discriminación. En BD: se calibrará.
ALTER TABLE normas.parametros_aprendizaje
    ADD COLUMN IF NOT EXISTS min_respuestas_discriminacion INTEGER NOT NULL DEFAULT 20;

COMMENT ON COLUMN normas.parametros_aprendizaje.min_respuestas_discriminacion IS
    'Respuestas necesarias para fiarse de la discriminación de un ítem. Por debajo, el dato es ruido y no se marca ninguna alerta.';

-- ── Verificación ──
SELECT alerta_calidad, COUNT(*)
FROM normas.preguntas_test WHERE revisada AND activa
GROUP BY alerta_calidad ORDER BY 1;
