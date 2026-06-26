-- ============================================================
-- Migración 020: Banco de preguntas + estructura multi-oposición
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

-- ── 1. Catálogo de oposiciones ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS normas.oposiciones (
    oposicion_id    SERIAL PRIMARY KEY,
    codigo          VARCHAR(20)    UNIQUE NOT NULL,
    nombre          TEXT           NOT NULL,
    nombre_corto    VARCHAR(50),
    n_preguntas     INTEGER        NOT NULL DEFAULT 100,
    tiempo_min      INTEGER        NOT NULL DEFAULT 90,
    penalizacion    NUMERIC(5,3)   NOT NULL DEFAULT 0.333,  -- E / 3
    activa          BOOLEAN        NOT NULL DEFAULT TRUE,
    creada_en       TIMESTAMP      NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE normas.oposiciones IS
    'Catálogo de convocatorias de oposición soportadas por la plataforma.';
COMMENT ON COLUMN normas.oposiciones.penalizacion IS
    'Factor de penalización por error: 0.333 = E/3 (fórmula GACE oficial).';

-- ── 2. Distribución de leyes por oposición ───────────────────────────────────
CREATE TABLE IF NOT EXISTS normas.oposicion_leyes (
    oposicion_id          INTEGER  NOT NULL REFERENCES normas.oposiciones(oposicion_id) ON DELETE CASCADE,
    ley_id                INTEGER  NOT NULL REFERENCES normas.leyes(ley_id) ON DELETE CASCADE,
    preguntas_simulacro   INTEGER  NOT NULL CHECK (preguntas_simulacro > 0),
    orden                 INTEGER  NOT NULL DEFAULT 0,  -- orden de presentación en la UI
    PRIMARY KEY (oposicion_id, ley_id)
);

COMMENT ON TABLE normas.oposicion_leyes IS
    'Qué leyes componen cada oposición y cuántas preguntas aportan al simulacro.';
COMMENT ON COLUMN normas.oposicion_leyes.preguntas_simulacro IS
    'Número de preguntas que se seleccionan de esta ley en un simulacro de 100.';

-- ── 3. Banco de preguntas generadas ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS normas.preguntas_test (
    pregunta_id   SERIAL       PRIMARY KEY,
    ley_id        INTEGER      NOT NULL REFERENCES normas.leyes(ley_id) ON DELETE CASCADE,
    titulo_id     INTEGER      REFERENCES normas.titulos(titulo_id) ON DELETE SET NULL,
    articulo      VARCHAR(20)  NOT NULL,
    pregunta      TEXT         NOT NULL,
    opcion_a      TEXT         NOT NULL,
    opcion_b      TEXT         NOT NULL,
    opcion_c      TEXT         NOT NULL,
    opcion_d      TEXT         NOT NULL,
    correcta      CHAR(1)      NOT NULL CHECK (correcta IN ('a','b','c','d')),
    explicacion   TEXT,
    revisada      BOOLEAN      NOT NULL DEFAULT FALSE,  -- aprobada por el formador
    activa        BOOLEAN      NOT NULL DEFAULT TRUE,   -- visible para alumnos
    generada_en   TIMESTAMP    NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE normas.preguntas_test IS
    'Banco de preguntas tipo test generadas por IA desde el texto oficial del BOE.';
COMMENT ON COLUMN normas.preguntas_test.revisada IS
    'TRUE = revisada y aprobada por el formador. Solo las revisadas se usan en simulacros.';
COMMENT ON COLUMN normas.preguntas_test.activa IS
    'FALSE = desactivada manualmente (pregunta incorrecta o duplicada).';

-- Índices para las consultas más frecuentes
CREATE INDEX IF NOT EXISTS idx_preguntas_ley
    ON normas.preguntas_test (ley_id);
CREATE INDEX IF NOT EXISTS idx_preguntas_titulo
    ON normas.preguntas_test (titulo_id);
CREATE INDEX IF NOT EXISTS idx_preguntas_revisada
    ON normas.preguntas_test (revisada, activa);
CREATE INDEX IF NOT EXISTS idx_preguntas_articulo
    ON normas.preguntas_test (ley_id, articulo);

-- ── 4. Datos iniciales: oposición GACE ───────────────────────────────────────
-- Distribución oficial según el programa GACE 2025 (verificar con convocatoria)
INSERT INTO normas.oposiciones
    (codigo, nombre, nombre_corto, n_preguntas, tiempo_min, penalizacion)
VALUES
    ('GACE',
     'Cuerpo de Gestión de la Administración Civil del Estado',
     'GACE',
     100, 90, 0.333)
ON CONFLICT (codigo) DO NOTHING;

-- Distribución de preguntas por ley en el simulacro GACE
-- Basada en el análisis real de los exámenes oficiales GACE 2024 y 2025.
-- ley_id 1=CE, 4=LPAC, 7=LRJSP, 8=TREBEP, 9=LGP, 12=LCSP
-- Total actual con 6 leyes: 51/100. Los 49 restantes proceden de leyes
-- pendientes de cargar: TUE/TFUE (~14), LOs institucionales (~5),
-- función pública complementaria (~10), otras leyes frecuentes (~13),
-- bloque de actualidad anual (~7).
INSERT INTO normas.oposicion_leyes
    (oposicion_id, ley_id, preguntas_simulacro, orden)
SELECT
    o.oposicion_id,
    l.ley_id,
    l.preguntas,
    l.orden
FROM normas.oposiciones o
CROSS JOIN (VALUES
    (1,  12, 1),   -- CE      → 12 preguntas (real GACE 2024/2025)
    (4,   6, 2),   -- LPAC    →  6 preguntas
    (7,   3, 3),   -- LRJSP   →  3 preguntas
    (8,  15, 4),   -- TREBEP  → 15 preguntas (TREBEP core + función pública ampliada)
    (9,  12, 5),   -- LGP     → 12 preguntas
    (12,  3, 6)    -- LCSP    →  3 preguntas
) AS l(ley_id, preguntas, orden)
WHERE o.codigo = 'GACE'
ON CONFLICT DO NOTHING;

-- ── 5. Verificación ──────────────────────────────────────────────────────────
SELECT
    o.codigo,
    o.nombre_corto,
    o.n_preguntas AS total_simulacro,
    COUNT(ol.ley_id)                 AS n_leyes,
    SUM(ol.preguntas_simulacro)      AS suma_preguntas,
    STRING_AGG(
        le.codigo || ' (' || ol.preguntas_simulacro || ')',
        ', ' ORDER BY ol.orden
    ) AS distribucion
FROM normas.oposiciones o
JOIN normas.oposicion_leyes ol ON o.oposicion_id = ol.oposicion_id
JOIN normas.leyes le           ON ol.ley_id      = le.ley_id
GROUP BY o.oposicion_id, o.codigo, o.nombre_corto, o.n_preguntas;
