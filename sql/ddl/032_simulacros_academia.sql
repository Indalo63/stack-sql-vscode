-- ============================================================
-- Migración 032: tabla normas.simulacros_academia + preguntas fijadas
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS normas.simulacros_academia (
    simulacro_id      BIGSERIAL    PRIMARY KEY,
    academia          TEXT,                                  -- para futuro multi-tenant; NULL = cliente único actual
    oposicion_id      INTEGER      NOT NULL REFERENCES normas.oposiciones(oposicion_id) ON DELETE CASCADE,
    nombre            TEXT         NOT NULL,
    estado            VARCHAR(20)  NOT NULL DEFAULT 'generado'
                      CHECK (estado IN ('generado', 'autorizado')),
    fecha_inicio      TIMESTAMPTZ  NOT NULL,
    fecha_fin         TIMESTAMPTZ  NOT NULL,
    autorizado_por    TEXT,                                  -- responsable de la academia que autorizó
    autorizado_en     TIMESTAMPTZ,
    generado_en       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CHECK (fecha_fin > fecha_inicio)
);

COMMENT ON TABLE normas.simulacros_academia IS
    'Simulacro con preguntas fijas idénticas para todos los alumnos de una academia, en una ventana temporal. La academia nunca genera preguntas (modelo de negocio: venta de lotes generados por la plataforma): solo puede leer el simulacro generado automáticamente y autorizarlo antes de que se abra la ventana.';
COMMENT ON COLUMN normas.simulacros_academia.academia IS
    'Identificador de la academia cliente. NULL mientras solo haya un cliente único; se formalizará con tabla propia cuando haya multi-tenant real.';
COMMENT ON COLUMN normas.simulacros_academia.estado IS
    'generado = preguntas seleccionadas automáticamente con la distribución oficial, pendiente de autorización. autorizado = el responsable de la academia lo aprobó; la selección de preguntas queda fija.';

-- ── Preguntas fijadas del simulacro (selección congelada tras autorizar) ─────
CREATE TABLE IF NOT EXISTS normas.simulacro_academia_preguntas (
    simulacro_id   BIGINT   NOT NULL REFERENCES normas.simulacros_academia(simulacro_id) ON DELETE CASCADE,
    pregunta_id    INTEGER  NOT NULL REFERENCES normas.preguntas_test(pregunta_id) ON DELETE RESTRICT,
    orden          INTEGER  NOT NULL,
    PRIMARY KEY (simulacro_id, pregunta_id)
);

COMMENT ON TABLE normas.simulacro_academia_preguntas IS
    'Lista fija de preguntas (mismo orden para todos los alumnos) de un simulacro de academia, generada automáticamente con la misma distribución oficial por ley que el simulacro personal.';

CREATE INDEX IF NOT EXISTS idx_simulacro_academia_preguntas_orden
    ON normas.simulacro_academia_preguntas (simulacro_id, orden);

CREATE INDEX IF NOT EXISTS idx_simulacros_academia_ventana
    ON normas.simulacros_academia (fecha_inicio, fecha_fin);

-- Verificación
SELECT COUNT(*) AS total_simulacros FROM normas.simulacros_academia;
