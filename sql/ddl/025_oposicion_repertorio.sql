-- ============================================================
-- Migración 025: Repertorio completo GACE en oposicion_leyes
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

-- ── 1. Ampliar CHECK para permitir peso 0
--       (en repertorio pero peso exacto pendiente de calibrar)
ALTER TABLE normas.oposicion_leyes
    DROP CONSTRAINT IF EXISTS oposicion_leyes_preguntas_simulacro_check;

ALTER TABLE normas.oposicion_leyes
    ADD CONSTRAINT oposicion_leyes_preguntas_simulacro_check
    CHECK (preguntas_simulacro >= 0);

-- ── 2. Insertar las 54 leyes restantes del repertorio GACE
--       preguntas_simulacro = 0 → en repertorio, pero peso de simulacro
--       pendiente de afinar (las 6 leyes núcleo ya tienen sus valores reales)
INSERT INTO normas.oposicion_leyes (oposicion_id, ley_id, preguntas_simulacro, orden)
SELECT
    o.oposicion_id,
    v.ley_id,
    0,
    v.orden
FROM normas.oposiciones o
CROSS JOIN (VALUES
    -- Normativa de la oposición (referencia interna, puede no estar en leyes)
    (14, 10),   -- GACE_NORM
    -- Institucional / Constitucional
    (15, 20),   -- LODP
    (17, 21),   -- LOTC
    (18, 22),   -- LGOB
    (19, 23),   -- LOCE
    (26, 24),   -- LOPJ
    (48, 25),   -- LOTCU
    -- Administración local
    (20, 30),   -- LBRL
    -- Transparencia y buen gobierno
    (21, 35),   -- LTBG
    -- Protección de datos
    (22, 36),   -- LOPD
    -- Presupuestaria / financiera
    (23, 40),   -- LOEPSF
    (31, 41),   -- LGT
    (29, 42),   -- LTPP
    (64, 43),   -- IGAE
    (65, 44),   -- ACF
    (66, 45),   -- PLJ
    -- Seguridad social / función pública complementaria
    (27, 50),   -- LGSS
    (42, 51),   -- RIRS
    (43, 52),   -- MUFACE
    (44, 53),   -- LMRFP
    (45, 54),   -- RDSA
    (46, 55),   -- RDRD
    (47, 56),   -- REGI
    (62, 57),   -- BCPSA
    (63, 58),   -- RRCP
    (70, 59),   -- LSSF
    -- Contratación y patrimonio
    (40, 60),   -- LPAP
    -- Subvenciones
    (38, 61),   -- LGS
    (61, 62),   -- RLGS
    -- Expropiación forzosa
    (39, 63),   -- LEF
    (60, 64),   -- RLEF
    -- Igualdad / género / diversidad
    (35, 70),   -- LOIEMH
    (36, 71),   -- LOIVG
    (50, 72),   -- LOIT
    (75, 73),   -- LTRANS
    (68, 74),   -- LGPD
    (69, 75),   -- LAEPD
    -- Jurisdicción contencioso-administrativa
    (37, 80),   -- LJCA
    -- Derecho laboral / empleo
    (49, 85),   -- ET
    (59, 86),   -- LE
    (71, 87),   -- LDEP
    -- Acción exterior / interoperabilidad
    (51, 90),   -- LASEE
    (53, 91),   -- ENI
    -- Código Civil
    (57, 95),   -- CC
    -- Derecho de la UE
    (33, 96),   -- TUE
    (34, 97),   -- TFUE
    -- Medioambiente y biodiversidad
    (58, 100),  -- LPNAT
    -- Telecomunicaciones
    (78, 101),  -- LGT22
    -- Educación / inmigración / asilo
    (72, 102),  -- LOE
    (73, 103),  -- LO4000
    (74, 104),  -- LASIL
    -- Unidad de mercado
    (77, 105),  -- LGUM
    -- Evaluación de políticas públicas
    (79, 106),  -- LEPP
    -- Consejo de Estado
    (67, 107)   -- ROCE
) AS v(ley_id, orden)
WHERE o.codigo = 'GACE'
AND EXISTS (SELECT 1 FROM normas.leyes l WHERE l.ley_id = v.ley_id)
ON CONFLICT DO NOTHING;

-- ── 3. Verificación
SELECT
    o.codigo,
    COUNT(ol.ley_id)                                              AS n_leyes_total,
    SUM(CASE WHEN ol.preguntas_simulacro > 0 THEN 1 ELSE 0 END)  AS n_leyes_nucleo,
    SUM(ol.preguntas_simulacro)                                   AS preguntas_nucleo
FROM normas.oposiciones o
JOIN normas.oposicion_leyes ol ON o.oposicion_id = ol.oposicion_id
WHERE o.codigo = 'GACE'
GROUP BY o.oposicion_id, o.codigo;
