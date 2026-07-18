-- ============================================================
-- Migración 052: cronómetro del simulacro y tiempo por pregunta
--
-- EL PROBLEMA QUE RESUELVE
-- El examen real es **100 preguntas en 90 minutos = 54 segundos por pregunta**.
-- Nuestro simulacro no tenía reloj, así que simulaba el examen **menos la
-- restricción que más aprobados se lleva por delante**: el tiempo. Un alumno
-- podía sacar un 40 sobre 50 en el simulacro tardando tres horas y llegar al
-- examen creyendo que lo tenía.
--
-- Y hay una destreza que sin reloj NO SE PUEDE ENTRENAR: repartir el tiempo.
-- Quedarse atascado en la pregunta 12 y no llegar a 20 preguntas del final
-- cuesta más puntos que no saberse un tema entero.
--
-- POR QUÉ HACE FALTA `blanco_por_tiempo` (y no basta con guardar el tiempo total)
-- En cuanto el reloj entrega el examen solo, aparece un tipo de blanco NUEVO:
-- el de la pregunta **a la que el alumno ni llegó**. Y ese blanco NO es lo
-- mismo que el blanco estratégico de la migración 050, aunque en la BD se
-- vieran idénticos (opcion_elegida NULL, correcta FALSE). Confundirlos rompe
-- tres cosas a la vez:
--
--   1. **El consejo al alumno se invierte.** `get_calibracion()` diagnostica
--      "exceso de prudencia: dejas en blanco lo que habrías acertado, contesta
--      más". Al que se quedó sin tiempo hay que decirle exactamente lo
--      contrario: "vas lento". Dos problemas opuestos, un mismo síntoma.
--
--   2. **Envenena la DIFICULTAD y la DISCRIMINACIÓN del ítem** (migraciones 047
--      y 049). Las preguntas del final del examen son a las que menos gente
--      llega. Si cada alumno que no llega deja una fila `correcta = FALSE`,
--      esas preguntas parecerán **imposibles** — y no es que sean difíciles, es
--      que nadie las ha leído. El detector de "preguntas rotas" empezaría a
--      señalar preguntas sanas por su POSICIÓN en el examen.
--
--   3. **Falsea el análisis de distractores**: un distractor no elegido porque
--      nadie llegó a la pregunta no es un "distractor muerto".
--
-- El criterio para marcarlo es conservador: solo se marca `blanco_por_tiempo`
-- la pregunta que el alumno **no tocó en absoluto** (ni respuesta, ni confianza
-- declarada) en un intento que se cerró **por agotarse el reloj**. Si la vio y
-- decidió callar, eso es una decisión estratégica y se respeta como tal.
--
-- LA DURACIÓN NO SE HARDCODEA
-- Sale de `convocatorias` (tiempo_minutos / num_preguntas), que ya existe desde
-- la migración 022. Un simulacro de 50 preguntas hereda 45 minutos. Si mañana
-- la convocatoria cambia el reloj, el simulacro cambia solo.
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

-- ── 1. El blanco que no fue una decisión ─────────────────────────────────────
ALTER TABLE normas.respuestas
    ADD COLUMN IF NOT EXISTS blanco_por_tiempo BOOLEAN NOT NULL DEFAULT FALSE;

-- Una pregunta contestada no puede ser un blanco por reloj.
ALTER TABLE normas.respuestas
    DROP CONSTRAINT IF EXISTS respuestas_blanco_tiempo_check;
ALTER TABLE normas.respuestas
    ADD CONSTRAINT respuestas_blanco_tiempo_check CHECK (
        NOT blanco_por_tiempo OR opcion_elegida IS NULL
    );

COMMENT ON COLUMN normas.respuestas.blanco_por_tiempo IS
    'TRUE = el alumno NO llegó a esta pregunta: se le agotó el tiempo sin tocarla. NO es un blanco estratégico (migración 050), y hay que excluirlo de la calibración, de la dificultad empírica, de la discriminación del ítem y del análisis de distractores: si no, las preguntas del FINAL del examen parecerán imposibles solo por estar al final.';

COMMENT ON COLUMN normas.respuestas.segundos IS
    'Segundos empleados en la pregunta, sellados al contestarla por primera vez (tiempo transcurrido desde la respuesta anterior). En un examen de una sola página, donde el alumno puede saltar y volver, es una APROXIMACIÓN: si se salta preguntas, el tiempo de leerlas se le atribuye a la siguiente que contesta. NULL = no cronometrado (repaso, o intentos anteriores a la migración 052).';

-- ── 2. El reloj del intento ──────────────────────────────────────────────────
ALTER TABLE normas.historial_simulacros
    ADD COLUMN IF NOT EXISTS segundos_empleados INTEGER;

ALTER TABLE normas.historial_simulacros
    ADD COLUMN IF NOT EXISTS segundos_limite INTEGER;

ALTER TABLE normas.historial_simulacros
    ADD COLUMN IF NOT EXISTS tiempo_agotado BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE normas.historial_simulacros
    ADD COLUMN IF NOT EXISTS sin_llegar INTEGER NOT NULL DEFAULT 0;

-- El ritmo NO se puede dividir entre las preguntas del examen: el que se queda
-- sin tiempo agota el reloj entero, así que "segundos / n_preguntas" le sale
-- clavado al ritmo objetivo y parece puntual **precisamente porque ha ido
-- lento**. El denominador honrado es el de las preguntas a las que LLEGÓ.
COMMENT ON COLUMN normas.historial_simulacros.sin_llegar IS
    'Preguntas que el alumno no llegó a tocar antes de que sonara el reloj. El ritmo real se mide sobre (n_preguntas - sin_llegar): dividir entre el total haría que quien agota el tiempo pareciera ir exactamente a ritmo de examen.';

-- Se quedan en NULL en los intentos anteriores al cronómetro. No se inventan:
-- aquellos simulacros no se hicieron contra reloj y su ritmo es desconocido.
COMMENT ON COLUMN normas.historial_simulacros.segundos_empleados IS
    'Tiempo real que empleó el alumno, de principio a entrega. NULL = intento sin cronómetro (anterior a la migración 052): su ritmo es desconocido y no se estima.';
COMMENT ON COLUMN normas.historial_simulacros.segundos_limite IS
    'Tiempo del que disponía, derivado de la convocatoria (tiempo_minutos/num_preguntas × n). Se guarda con el intento para que el ritmo siga siendo interpretable aunque mañana cambie la convocatoria.';
COMMENT ON COLUMN normas.historial_simulacros.tiempo_agotado IS
    'TRUE = el simulacro lo cerró el reloj, no el alumno. Sus preguntas sin tocar quedan marcadas con respuestas.blanco_por_tiempo.';

-- ── 3. Verificación ──────────────────────────────────────────────────────────
SELECT
    (SELECT COUNT(*) FROM normas.respuestas WHERE blanco_por_tiempo)          AS blancos_por_reloj,
    (SELECT COUNT(*) FROM normas.historial_simulacros WHERE tiempo_agotado)   AS intentos_agotados,
    (SELECT COUNT(*) FROM normas.historial_simulacros
      WHERE segundos_empleados IS NULL)                                        AS intentos_sin_cronometro;
