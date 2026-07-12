-- ============================================================
-- Migración 045: nueva regla de dominio de un tema
--
-- QUÉ PROBLEMA RESUELVE
-- La regla anterior era:  estudiado = (vistas > 0) AND (correctas/vistas >= 70%)
-- Tenía TRES fallos, y no eran de calibración sino de fondo:
--
--   1. RUIDO. Con `vistas > 0`, un tema con DOS respuestas ya contaba. Dos fallos
--      por mala suerte bloqueaban el bloque entero. (Medido en la simulación del
--      12/07/2026: un tema con 2 vistas y 0% bloqueaba un bloque que iba al 78%.)
--
--   2. CASTIGABA EL APRENDIZAJE. El porcentaje era ACUMULADO de toda la vida. Si
--      el alumno fallaba una pregunta 5 veces y luego la dominaba, su porcentaje
--      seguía hundido para siempre. Es pedagógicamente al revés: usamos
--      repetición espaciada (SM-2) precisamente porque fallar y reaprender ES
--      aprender… y luego lo evaluábamos con una métrica que lo penaliza.
--
--   3. AGUJERO DE COBERTURA (en sentido contrario). Los temas nunca practicados
--      no contaban en contra, así que un alumno podía practicar UN solo tema del
--      bloque, sacar 70%, y el bloque quedaba "estudiado" ignorando los otros 9.
--
-- LA REGLA NUEVA
--   Tema DOMINADO   = (preguntas distintas vistas >= muestra_minima)
--                     AND (>= umbral_dominio % de ellas ASENTADAS en SM-2)
--   Asentada        = repeticiones >= 2  (acertada 2+ veces seguidas, en momentos
--                     distintos; al fallar, SM-2 resetea repeticiones a 0)
--   Bloque ESTUDIADO= (>= cobertura_bloque % de sus temas CON BANCO SUFICIENTE
--                     están evaluados) AND (ninguno evaluado por debajo del umbral)
--
-- Es MÁS EXIGENTE que la anterior (hay que acertar la misma pregunta dos veces
-- separadas en el tiempo, y no se puede ignorar la mayoría de los temas) y a la
-- vez MÁS JUSTA (el que falla, repasa y acaba dominando, cuenta como que domina).
--
-- Y sobre todo: el estado del SM-2 es la ÚNICA métrica proyectable al día del
-- examen (guarda intervalo y proxima_revision = un modelo de la curva de olvido).
-- Un porcentaje histórico no se puede proyectar. Esto es lo que hará posible el
-- "¿estoy listo para el examen?" (Fase 5.2), que la competencia vende y nosotros
-- no podríamos calcular con la métrica antigua.
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

-- ── 1. Parámetros en BD, no en código (norma del proyecto) ───────────────────
CREATE TABLE IF NOT EXISTS normas.parametros_aprendizaje (
    oposicion_id      INTEGER PRIMARY KEY REFERENCES normas.oposiciones(oposicion_id) ON DELETE CASCADE,
    muestra_minima    INTEGER NOT NULL DEFAULT 5,    -- preguntas distintas para evaluar un tema
    umbral_dominio    INTEGER NOT NULL DEFAULT 70,   -- % de ellas que deben estar asentadas
    repeticiones_ok   INTEGER NOT NULL DEFAULT 2,    -- aciertos seguidos para considerarla asentada
    cobertura_bloque  INTEGER NOT NULL DEFAULT 60,   -- % de temas del bloque que hay que haber evaluado
    actualizado_en    TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT param_apr_muestra    CHECK (muestra_minima  >= 1),
    CONSTRAINT param_apr_umbral     CHECK (umbral_dominio  BETWEEN 1 AND 100),
    CONSTRAINT param_apr_reps       CHECK (repeticiones_ok >= 1),
    CONSTRAINT param_apr_cobertura  CHECK (cobertura_bloque BETWEEN 0 AND 100)
);

COMMENT ON TABLE normas.parametros_aprendizaje IS
    'Parámetros de la regla de dominio (migración 045). En BD y no en código para poder calibrarlos con datos reales de alumnos sin desplegar.';
COMMENT ON COLUMN normas.parametros_aprendizaje.muestra_minima IS
    'Preguntas DISTINTAS que hay que haber visto en un tema para que su dominio signifique algo. Por debajo, el tema no se evalúa: ni bloquea ni cuenta como dominado.';
COMMENT ON COLUMN normas.parametros_aprendizaje.repeticiones_ok IS
    'Aciertos seguidos (SM-2) para dar una pregunta por asentada. Al fallar, SM-2 resetea repeticiones a 0, así que esto mide el dominio ACTUAL, no el historial.';

INSERT INTO normas.parametros_aprendizaje (oposicion_id) VALUES (1)
ON CONFLICT (oposicion_id) DO NOTHING;

-- ── 2. plan_estudio guarda el dominio, además del acierto histórico ──────────
-- El % de acierto se conserva: sigue siendo útil para MOSTRAR al alumno cómo le
-- va. Pero ya NO decide si el tema está dominado.
ALTER TABLE normas.plan_estudio
    ADD COLUMN IF NOT EXISTS preguntas_distintas INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS preguntas_asentadas INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS dominio_pct         NUMERIC(5,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS evaluable           BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN normas.plan_estudio.preguntas_distintas IS
    'Preguntas distintas vistas en el tema (no respuestas: el SM-2 re-sirve las falladas).';
COMMENT ON COLUMN normas.plan_estudio.preguntas_asentadas IS
    'Cuántas de ellas están asentadas en SM-2 (repeticiones >= repeticiones_ok).';
COMMENT ON COLUMN normas.plan_estudio.dominio_pct IS
    'asentadas / distintas. ESTA es la métrica que decide si el tema está dominado (no porcentaje_acierto, que es histórico y castiga al que falla y luego aprende).';
COMMENT ON COLUMN normas.plan_estudio.evaluable IS
    'TRUE si el tema tiene muestra suficiente (>= muestra_minima). Los no evaluables ni bloquean ni cuentan como dominados.';

-- ── Verificación ──
SELECT muestra_minima, umbral_dominio, repeticiones_ok, cobertura_bloque
FROM normas.parametros_aprendizaje WHERE oposicion_id = 1;
