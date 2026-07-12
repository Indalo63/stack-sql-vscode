-- ============================================================
-- Migración 044: recálculo autorizado de los pesos de bloque
--
-- MOTIVO:
-- Los pesos de bloque (migración 042) son una FOTO FIJA de los exámenes
-- oficiales cargados hoy (GACE 2024 y 2025). Si mañana se carga el examen de
-- 2023, el reparto real cambia y el objetivo del banco debería cambiar con él.
--
-- Pero **el recálculo NO debe ser automático**: un examen cargado con errores
-- desviaría los pesos en silencio, y con ellos el motor (prueba de nivel,
-- simulacros) y el objetivo del banco. Por eso se propone y **un administrador
-- lo autoriza** explícitamente.
--
-- ⚠️ COHERENCIA — el peso vive en DOS sitios y hay que actualizar los dos:
--   1. `oposicion_leyes.preguntas_simulacro` -> lo usa el MOTOR (reparto de la
--      prueba de nivel y de los simulacros).
--   2. `objetivo_banco.peso_examen` + `objetivo` -> lo usa el CONTROL de
--      cobertura del banco.
-- Si solo se tocara uno, el simulacro repartiría con unos pesos y el objetivo
-- del banco perseguiría otros.
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

-- ── 1. El "suelo" pasa a ser un parámetro de BD, no una constante ────────────
CREATE TABLE IF NOT EXISTS normas.parametros_banco (
    oposicion_id     INTEGER PRIMARY KEY REFERENCES normas.oposiciones(oposicion_id) ON DELETE CASCADE,
    suelo_bloque_min INTEGER NOT NULL DEFAULT 200,
    actualizado_en   TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT parametros_banco_suelo_check CHECK (suelo_bloque_min > 0)
);

COMMENT ON TABLE normas.parametros_banco IS
    'Parámetros del objetivo del banco, en BD y no en código (norma del proyecto: nada de convocatoria hardcodeado).';
COMMENT ON COLUMN normas.parametros_banco.suelo_bloque_min IS
    'Preguntas mínimas que debe tener el bloque MÁS PEQUEÑO del examen. El resto de bloques escalan proporcionalmente a su peso. Con suelo=200 y el bloque menor al 11%, el objetivo total sale ~1.819.';

INSERT INTO normas.parametros_banco (oposicion_id, suelo_bloque_min)
VALUES (1, 200)
ON CONFLICT (oposicion_id) DO NOTHING;

-- ── 2. Histórico de recálculos (auditoría) ───────────────────────────────────
CREATE TABLE IF NOT EXISTS normas.historial_pesos (
    recalculo_id   SERIAL PRIMARY KEY,
    oposicion_id   INTEGER NOT NULL REFERENCES normas.oposiciones(oposicion_id) ON DELETE CASCADE,
    aplicado_por   VARCHAR(150) NOT NULL,   -- email del admin que lo autorizó
    aplicado_en    TIMESTAMP NOT NULL DEFAULT NOW(),
    examenes       TEXT NOT NULL,           -- qué exámenes sustentan el cálculo
    n_preguntas    INTEGER NOT NULL,        -- sobre cuántas preguntas se midió
    suelo          INTEGER NOT NULL,
    pesos_antes    JSONB,                   -- {"I":21,...} antes del cambio
    pesos_despues  JSONB NOT NULL           -- {"I":21,...} después
);

COMMENT ON TABLE normas.historial_pesos IS
    'Cada recálculo de pesos de bloque autorizado por un administrador. Permite saber por qué cambió el objetivo del banco, y volver atrás si un examen se cargó con errores.';

CREATE INDEX IF NOT EXISTS idx_historial_pesos_oposicion
    ON normas.historial_pesos (oposicion_id, aplicado_en DESC);

-- ── Verificación ──
SELECT oposicion_id, suelo_bloque_min FROM normas.parametros_banco;
SELECT COUNT(*) AS recalculos_registrados FROM normas.historial_pesos;
