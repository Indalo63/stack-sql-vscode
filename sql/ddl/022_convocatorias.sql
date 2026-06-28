-- ============================================================
-- Migración 022: Tabla estructurada de convocatorias
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

-- ── 1. Tabla principal ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS normas.convocatorias (
    año                  VARCHAR(4)    PRIMARY KEY,
    oposicion_id         INTEGER       REFERENCES normas.oposiciones(oposicion_id),
    cuerpo               VARCHAR(200)  NOT NULL,
    sistema              VARCHAR(20)   NOT NULL DEFAULT 'ingreso_libre'
                             CHECK (sistema IN ('ingreso_libre', 'promocion_interna')),
    num_plazas           INTEGER,
    resolucion           TEXT,
    fecha_resolucion     DATE,

    -- Primer ejercicio
    num_preguntas        INTEGER       NOT NULL DEFAULT 100,
    num_reserva          INTEGER       NOT NULL DEFAULT 5,
    tiempo_minutos       INTEGER       NOT NULL DEFAULT 90,

    -- Fórmula de puntuación
    formula              VARCHAR(50)   NOT NULL DEFAULT 'A-(E/3)',
    valor_acierto        NUMERIC(6,4)  NOT NULL DEFAULT 1.0,
    penalizacion_error   NUMERIC(6,4)  NOT NULL DEFAULT 0.3333,
    penalizacion_blanco  NUMERIC(6,4)  NOT NULL DEFAULT 0.0,

    -- Calificación
    escala_min           NUMERIC(5,2)  NOT NULL DEFAULT 0,
    escala_max           NUMERIC(5,2)  NOT NULL DEFAULT 50,
    nota_minima          NUMERIC(5,2)  NOT NULL DEFAULT 25,
    pct_aprobado         NUMERIC(5,2)  NOT NULL DEFAULT 50,
    pct_corte_minimo     NUMERIC(5,2)  NOT NULL DEFAULT 30,

    created_at           TIMESTAMPTZ   DEFAULT NOW()
);

COMMENT ON TABLE normas.convocatorias IS
    'Metadatos estructurados de cada convocatoria GACE: fórmula, tiempo, nota mínima.';

-- ── 2. Datos convocatoria 2024 ────────────────────────────────────────────────
INSERT INTO normas.convocatorias (
    año, oposicion_id, cuerpo, sistema,
    num_plazas, resolucion, fecha_resolucion,
    num_preguntas, num_reserva, tiempo_minutos,
    formula, valor_acierto, penalizacion_error, penalizacion_blanco,
    escala_min, escala_max, nota_minima, pct_aprobado, pct_corte_minimo
) VALUES (
    '2024',
    (SELECT oposicion_id FROM normas.oposiciones WHERE codigo = 'GACE' LIMIT 1),
    'Cuerpo de Gestión de la Administración Civil del Estado',
    'ingreso_libre',
    2754,
    'Resolución de 9 de julio de 2024, de la Secretaría de Estado de Función Pública',
    '2024-07-09',
    100, 5, 90,
    'A-(E/3)', 1.0, 0.3333, 0.0,
    0, 50, 25, 50, 30
)
ON CONFLICT (año) DO NOTHING;

-- ── 3. Datos convocatoria 2025 ────────────────────────────────────────────────
INSERT INTO normas.convocatorias (
    año, oposicion_id, cuerpo, sistema,
    num_plazas, resolucion, fecha_resolucion,
    num_preguntas, num_reserva, tiempo_minutos,
    formula, valor_acierto, penalizacion_error, penalizacion_blanco,
    escala_min, escala_max, nota_minima, pct_aprobado, pct_corte_minimo
) VALUES (
    '2025',
    (SELECT oposicion_id FROM normas.oposiciones WHERE codigo = 'GACE' LIMIT 1),
    'Cuerpo de Gestión de la Administración Civil del Estado',
    'ingreso_libre',
    1356,
    'Resolución de 18 de diciembre de 2025, de la Secretaría de Estado de Función Pública',
    '2025-12-18',
    100, 5, 90,
    'A-(E/3)', 1.0, 0.3333, 0.0,
    0, 50, 25, 50, 30
)
ON CONFLICT (año) DO NOTHING;

-- ── 4. Verificación ───────────────────────────────────────────────────────────
SELECT
    c.año,
    c.num_plazas,
    c.num_preguntas,
    c.tiempo_minutos,
    c.formula,
    c.nota_minima,
    c.pct_aprobado       AS "% aprueba",
    c.pct_corte_minimo   AS "% corte mín",
    o.nombre             AS oposicion
FROM normas.convocatorias c
LEFT JOIN normas.oposiciones o ON o.oposicion_id = c.oposicion_id
ORDER BY c.año;
