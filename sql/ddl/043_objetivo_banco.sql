-- ============================================================
-- Migración 043: objetivo de cobertura del banco por bloque
--
-- MOTIVO (detectado el 12/07/2026):
-- El banco está **muy sesgado** respecto al examen real. Se generaba donde
-- resultaba cómodo, no donde cae el examen:
--
--   Bloque   banco   % banco   % examen   desfase
--     I        36     14,8%      21%       -6,2   FALTA
--     II       38     15,6%      12%       +3,6
--     III      14      5,8%      11%       -5,2   FALTA
--     IV       86     35,4%      20%      +15,4   SOBRA
--     V        26     10,7%      21%      -10,3   FALTA (¡pesa igual que el I!)
--     VI       43     17,7%      15%       +2,7
--
-- El bloque IV acaparaba el 35% del banco teniendo el 20% del examen, mientras
-- que el V (que pesa lo mismo que el I, el máximo) tenía la mitad de lo que le
-- toca. Sin un objetivo explícito, el banco no converge nunca al examen.
--
-- CÓMO SE CALCULA EL OBJETIVO (decisión del usuario, 12/07/2026):
--   - Se respeta el **peso real del examen** (migración 042, derivado de los
--     exámenes oficiales 2024+2025 por posición: I=21, II=12, III=11, IV=20,
--     V=21, VI=15).
--   - Con un **suelo de 200 preguntas en el bloque más pequeño** (III, 11%).
--   - El resto escala proporcionalmente:  objetivo = peso * (200 / 11)
--
--   Bloque   peso   objetivo
--     I       21      382
--     II      12      218
--     III     11      200   <- el suelo
--     IV      20      364
--     V       21      382
--     VI      15      273
--                    ----
--                    1.819
--
-- El objetivo vive en BD, no en código: cambiar la meta o dar de alta otra
-- oposición no debe exigir tocar código (norma del proyecto).
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS normas.objetivo_banco (
    oposicion_id  INTEGER NOT NULL REFERENCES normas.oposiciones(oposicion_id) ON DELETE CASCADE,
    bloque        VARCHAR(4) NOT NULL,
    peso_examen   INTEGER NOT NULL,   -- % del examen real (suma 100)
    objetivo      INTEGER NOT NULL,   -- nº mínimo de preguntas revisadas en el banco
    PRIMARY KEY (oposicion_id, bloque),
    CONSTRAINT objetivo_banco_peso_check     CHECK (peso_examen BETWEEN 0 AND 100),
    CONSTRAINT objetivo_banco_objetivo_check CHECK (objetivo >= 0)
);

COMMENT ON TABLE normas.objetivo_banco IS
    'Distribución MÍNIMA que debe tener el banco de preguntas por bloque, para que refleje el peso real del examen. Sin esto el banco se sesga hacia donde es cómodo generar. peso_examen sale de los exámenes oficiales (migración 042); objetivo = peso * (suelo / peso_menor).';
COMMENT ON COLUMN normas.objetivo_banco.peso_examen IS
    'Porcentaje del examen real que representa este bloque (medido sobre los exámenes oficiales cargados). La suma de todos los bloques es 100.';
COMMENT ON COLUMN normas.objetivo_banco.objetivo IS
    'Preguntas revisadas que debe tener el banco en este bloque, como mínimo. Deriva del peso del examen con un suelo de 200 en el bloque más pequeño.';

INSERT INTO normas.objetivo_banco (oposicion_id, bloque, peso_examen, objetivo) VALUES
    (1, 'I',   21, 382),
    (1, 'II',  12, 218),
    (1, 'III', 11, 200),   -- el suelo: bloque más pequeño
    (1, 'IV',  20, 364),
    (1, 'V',   21, 382),
    (1, 'VI',  15, 273)
ON CONFLICT (oposicion_id, bloque) DO UPDATE
    SET peso_examen = EXCLUDED.peso_examen,
        objetivo    = EXCLUDED.objetivo;

-- ── Verificación: estado real del banco frente al objetivo ──
SELECT ob.bloque,
       ob.peso_examen                                   AS pct_examen,
       COUNT(pt.pregunta_id)                            AS banco_actual,
       ob.objetivo,
       ob.objetivo - COUNT(pt.pregunta_id)              AS faltan
FROM normas.objetivo_banco ob
LEFT JOIN normas.oposicion_leyes ol
       ON ol.oposicion_id = ob.oposicion_id
      AND ol.bloque = ob.bloque
      AND NOT ol.excluir_test
LEFT JOIN normas.preguntas_test pt
       ON pt.ley_id = ol.ley_id
      AND pt.revisada AND pt.activa
WHERE ob.oposicion_id = 1
GROUP BY ob.bloque, ob.peso_examen, ob.objetivo
ORDER BY ob.bloque;
