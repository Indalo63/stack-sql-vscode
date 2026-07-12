-- ============================================================
-- Migración 050: confianza declarada y decisión de dejar en blanco
--
-- EL PROBLEMA QUE RESUELVE
-- La fórmula oficial de GACE es **A − E/3**: fallar RESTA, dejar en blanco no.
-- Eso convierte "¿contesto o callo?" en una **decisión estratégica** que se puede
-- entrenar — y que ningún competidor entrena.
--
-- Hoy medimos si el alumno acierta. No medimos si SABE lo que sabe. Son cosas
-- distintas, y la segunda es la que decide puntos en el examen real:
--
--   · **Exceso de confianza**: falla justo cuando está seguro. Es el perfil más
--     peligroso, porque ni siquiera repasa lo que cree dominar.
--   · **Exceso de prudencia**: deja en blanco preguntas que habría acertado.
--     Regala puntos por miedo a una penalización que, en realidad, no le sale
--     a cuenta evitar.
--
-- Sin preguntarle su confianza ANTES de corregir, ninguna de las dos se puede
-- detectar: acertar por saberlo y acertar por suerte se ven exactamente igual
-- en los datos.
--
-- LA MATEMÁTICA (se deriva de `convocatorias`, NO se hardcodea)
-- Responder sale a cuenta cuando la probabilidad de acierto `p` supera
--     p* = (penalizacion_error − penalizacion_blanco) / (valor_acierto + penalizacion_error)
-- Con la fórmula GACE (1, 1/3, 0):  p* = (1/3) / (4/3) = **0,25**.
--
-- Es decir: **responder al azar entre 4 opciones es exactamente neutro** (ni
-- suma ni resta), y en cuanto el alumno puede descartar UNA sola opción su
-- probabilidad sube a 1/3 y responder ya GANA puntos. La creencia popular de
-- "ante la duda, en blanco" es, con esta fórmula, **matemáticamente falsa**.
--
-- Pero el umbral teórico asume que los distractores no arrastran. Y arrastran:
-- están diseñados para eso. Por eso hace falta el dato REAL de cada alumno —
-- qué porcentaje acierta él cuando dice "ni idea" — y compararlo con p*.
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

ALTER TABLE normas.respuestas
    ADD COLUMN IF NOT EXISTS confianza VARCHAR(8);

ALTER TABLE normas.respuestas
    DROP CONSTRAINT IF EXISTS respuestas_confianza_check;
ALTER TABLE normas.respuestas
    ADD CONSTRAINT respuestas_confianza_check CHECK (
        confianza IS NULL OR confianza IN ('seguro', 'dudo', 'ni_idea')
    );

COMMENT ON COLUMN normas.respuestas.confianza IS
    'Confianza que el alumno DECLARÓ antes de ver la corrección: seguro | dudo | ni_idea. NULL = no la declaró (no se le pidió, o la omitió: es opcional). Cruzada con `correcta` da la CALIBRACIÓN (¿sabe lo que sabe?); cruzada con `opcion_elegida IS NULL` da si deja en blanco lo que habría acertado.';

CREATE INDEX IF NOT EXISTS idx_respuestas_confianza
    ON normas.respuestas (user_id, confianza) WHERE confianza IS NOT NULL;

-- Respuestas necesarias en un nivel de confianza para fiarse del diagnóstico.
-- Con 4 respuestas, un 50% de acierto es ruido. En BD: se calibrará con alumnos.
ALTER TABLE normas.parametros_aprendizaje
    ADD COLUMN IF NOT EXISTS min_respuestas_calibracion INTEGER NOT NULL DEFAULT 10;

COMMENT ON COLUMN normas.parametros_aprendizaje.min_respuestas_calibracion IS
    'Respuestas necesarias en un nivel de confianza para dar un diagnóstico de calibración. Por debajo, el porcentaje es ruido y no se le dice nada al alumno (un consejo mal fundado es peor que ninguno).';

-- ── Verificación ──
SELECT confianza,
       COUNT(*)                                        AS respuestas,
       COUNT(*) FILTER (WHERE correcta)                AS aciertos,
       COUNT(*) FILTER (WHERE opcion_elegida IS NULL)  AS en_blanco
FROM normas.respuestas
GROUP BY confianza ORDER BY 1;
