-- ============================================================
-- Migración 026: Asignación de bloques del programa GACE
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

-- ── 1. Añadir columna bloque
ALTER TABLE normas.oposicion_leyes
    ADD COLUMN IF NOT EXISTS bloque VARCHAR(5);

-- ── 2. Asignar bloques según el programa oficial GACE 2025
-- Bloque I: Organización del Estado y de la Administración Pública
UPDATE normas.oposicion_leyes ol SET bloque = 'I'
FROM normas.oposiciones o
WHERE ol.oposicion_id = o.oposicion_id AND o.codigo = 'GACE'
  AND ol.ley_id IN (
    1,   -- CE
    14,  -- GACE_NORM
    15,  -- LODP
    17,  -- LOTC
    18,  -- LGOB
    19,  -- LOCE
    20,  -- LBRL
    26,  -- LOPJ
    67   -- ROCE
);

-- Bloque II: Unión Europea
UPDATE normas.oposicion_leyes ol SET bloque = 'II'
FROM normas.oposiciones o
WHERE ol.oposicion_id = o.oposicion_id AND o.codigo = 'GACE'
  AND ol.ley_id IN (
    33,  -- TUE
    34   -- TFUE
);

-- Bloque III: Políticas Públicas
UPDATE normas.oposicion_leyes ol SET bloque = 'III'
FROM normas.oposiciones o
WHERE ol.oposicion_id = o.oposicion_id AND o.codigo = 'GACE'
  AND ol.ley_id IN (
    21,  -- LTBG
    22,  -- LOPD
    27,  -- LGSS
    35,  -- LOIEMH
    36,  -- LOIVG
    50,  -- LOIT
    51,  -- LASEE
    53,  -- ENI
    58,  -- LPNAT
    59,  -- LE
    68,  -- LGPD
    71,  -- LDEP
    72,  -- LOE
    73,  -- LO4000
    74,  -- LASIL
    75,  -- LTRANS
    77,  -- LGUM
    78,  -- LGT22
    79   -- LEPP
);

-- Bloque IV: Derecho Administrativo General
UPDATE normas.oposicion_leyes ol SET bloque = 'IV'
FROM normas.oposiciones o
WHERE ol.oposicion_id = o.oposicion_id AND o.codigo = 'GACE'
  AND ol.ley_id IN (
    4,   -- LPAC
    7,   -- LRJSP
    12,  -- LCSP
    37,  -- LJCA
    38,  -- LGS
    39,  -- LEF
    40,  -- LPAP
    57,  -- CC
    60,  -- RLEF
    61   -- RLGS
);

-- Bloque V: Administración de Recursos Humanos
UPDATE normas.oposicion_leyes ol SET bloque = 'V'
FROM normas.oposiciones o
WHERE ol.oposicion_id = o.oposicion_id AND o.codigo = 'GACE'
  AND ol.ley_id IN (
    8,   -- TREBEP
    42,  -- RIRS
    43,  -- MUFACE
    44,  -- LMRFP
    45,  -- RDSA
    46,  -- RDRD
    47,  -- REGI
    49,  -- ET
    62,  -- BCPSA
    63,  -- RRCP
    69,  -- LAEPD
    70   -- LSSF
);

-- Bloque VI: Gestión Financiera y Seguridad Social
UPDATE normas.oposicion_leyes ol SET bloque = 'VI'
FROM normas.oposiciones o
WHERE ol.oposicion_id = o.oposicion_id AND o.codigo = 'GACE'
  AND ol.ley_id IN (
    9,   -- LGP
    23,  -- LOEPSF
    29,  -- LTPP
    31,  -- LGT
    48,  -- LOTCU
    64,  -- IGAE
    65,  -- ACF
    66   -- PLJ
);

-- ── 3. Verificación
SELECT
    ol.bloque,
    COUNT(*)                              AS n_leyes,
    STRING_AGG(l.codigo, ', ' ORDER BY ol.orden) AS leyes
FROM normas.oposicion_leyes ol
JOIN normas.oposiciones o ON o.oposicion_id = ol.oposicion_id
JOIN normas.leyes l       ON l.ley_id       = ol.ley_id
WHERE o.codigo = 'GACE'
GROUP BY ol.bloque
ORDER BY ol.bloque;
