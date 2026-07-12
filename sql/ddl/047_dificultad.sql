-- ============================================================
-- Migración 047: dificultad de las preguntas (provisional → empírica)
--
-- EL PROBLEMA
-- Las 297 preguntas tenían `dificultad = 2` (el valor por defecto): el campo
-- existía pero NUNCA se usó. El `ORDER BY dificultad` de la prueba de nivel no
-- ordenaba nada, así que la promesa que se le hacía al alumno ("40 preguntas de
-- dificultad creciente") era FALSA. Y el editor tampoco podía asignarla: el campo
-- nunca llegó a la pantalla de revisión.
--
-- POR QUÉ NO BASTA CON QUE ALGUIEN LA MARQUE A MANO
-- La dificultad de un ítem **no es una opinión editorial: es una propiedad
-- empírica**. En teoría de test se DEFINE como la proporción de examinandos que
-- lo acierta. Y los expertos son notoriamente malos estimándola: cuando ya sabes
-- la respuesta, no ves por qué es difícil ("maldición del conocimiento"). Un
-- editor —o una IA— marcando "esta parece difícil" está adivinando.
--
-- LA SOLUCIÓN: HÍBRIDA Y AUTOCORRECTIVA
--   1. `dificultad_origen = 'heuristica'` -> valor PROVISIONAL, calculado con
--      señales objetivas del texto (¿pide un dato exacto? ¿los distractores se
--      parecen mucho entre sí?). Sirve para que el orden funcione HOY.
--   2. `dificultad_origen = 'empirica'`   -> valor REAL, calculado con el % de
--      acierto de los alumnos, en cuanto la pregunta acumule suficientes
--      respuestas. **Sustituye a la heurística**: el dato manda sobre la
--      conjetura.
--
-- Es autocorrectivo: cuantos más alumnos, más exacta. Es lo que hacen las
-- plataformas serias de test.
--
-- ⚠️ La heurística NO está validada (no puede estarlo sin alumnos). Por eso queda
-- marcada como tal en `dificultad_origen`: para que nadie la confunda con un dato.
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

ALTER TABLE normas.preguntas_test
    ADD COLUMN IF NOT EXISTS dificultad_origen VARCHAR(12) NOT NULL DEFAULT 'default',
    ADD COLUMN IF NOT EXISTS dificultad_n      INTEGER     NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS dificultad_pct    NUMERIC(5,2);

ALTER TABLE normas.preguntas_test
    DROP CONSTRAINT IF EXISTS preguntas_dificultad_origen_check;
ALTER TABLE normas.preguntas_test
    ADD CONSTRAINT preguntas_dificultad_origen_check
        CHECK (dificultad_origen IN ('default', 'heuristica', 'empirica'));

COMMENT ON COLUMN normas.preguntas_test.dificultad_origen IS
    'default = nunca se calculó. heuristica = valor PROVISIONAL de señales del texto (una conjetura, no un dato). empirica = valor REAL medido con el acierto de los alumnos; manda sobre la heurística.';
COMMENT ON COLUMN normas.preguntas_test.dificultad_n IS
    'Respuestas de alumnos sobre las que se calculó la dificultad empírica. 0 si aún es heurística.';
COMMENT ON COLUMN normas.preguntas_test.dificultad_pct IS
    'Porcentaje de acierto real (índice de dificultad clásico: cuanto MÁS alto, más fácil). NULL si aún no hay datos.';

-- Umbral de respuestas para que el dato real sustituya a la conjetura.
-- En BD, no en código: se calibrará con alumnos reales.
ALTER TABLE normas.parametros_aprendizaje
    ADD COLUMN IF NOT EXISTS min_respuestas_dificultad INTEGER NOT NULL DEFAULT 20;

COMMENT ON COLUMN normas.parametros_aprendizaje.min_respuestas_dificultad IS
    'Respuestas necesarias para fiarse del acierto real de una pregunta y sustituir la heurística. Por debajo, el dato es ruido.';

-- ── Verificación ──
SELECT dificultad_origen, dificultad, COUNT(*)
FROM normas.preguntas_test WHERE revisada AND activa
GROUP BY dificultad_origen, dificultad ORDER BY 1, 2;
