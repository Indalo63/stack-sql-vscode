-- ============================================================
-- Migración 042: pesos de bloque corregidos (reparto real del examen)
--
-- BUG QUE CORRIGE (detectado el 12/07/2026 al preparar el MVP):
-- Los bloques II (Unión Europea) y III (Políticas Públicas) tenían
-- `preguntas_simulacro = 0` en TODAS sus leyes, pese a tener preguntas cargadas
-- (TFUE: 23, TUE: 15). Y la suma de todos los pesos era 51, no 100.
--
-- Consecuencia en cadena, que habría arruinado la prueba con alumnos:
--   1. La prueba de nivel reparte proporcionalmente al peso -> nunca servía
--      preguntas de los bloques II y III.
--   2. El simulacro personal exige tener datos en LOS 6 bloques.
--   3. Por tanto el simulacro personal quedaba BLOQUEADO PARA SIEMPRE.
--
-- DE DÓNDE SALEN ESTOS PESOS (no están inventados):
-- Del reparto real de los exámenes oficiales GACE 2024 y 2025 (209 preguntas),
-- que ya están cargados. Método determinista, sin IA: **los exámenes están
-- ordenados por bloque** (I -> II -> III -> IV -> V -> VI, igual que el
-- programa), así que el bloque de las preguntas sin ley asignada (actualidad y
-- normas no cargadas) se deduce por su POSICIÓN entre preguntas ya clasificadas.
--
-- Esto corrige un sesgo importante: el cálculo ingenuo (solo preguntas con ley
-- asignada) INFRAVALORA a los bloques II y III, precisamente porque su
-- contenido apunta a normas que no tenemos cargadas.
--
--   Bloque   preguntas   % examen   peso
--     I          42        21,4%      21
--     II         23        11,7%      12
--     III        21        10,7%      11
--     IV         39        19,9%      20
--     V          42        21,4%      21
--     VI         29        14,8%      15
--                                    ---
--                                    100
--
-- El peso de cada bloque se reparte entre sus leyes en proporción a las veces
-- que cada una aparece en los exámenes oficiales. Las leyes que no aparecen en
-- ninguno de los dos exámenes quedan a 0 (no se inventa una frecuencia).
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

-- Punto de partida limpio
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 0 WHERE oposicion_id = 1;

UPDATE normas.oposicion_leyes SET preguntas_simulacro = 14 WHERE oposicion_id=1 AND ley_id=1;  -- CE1978 (25 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 2 WHERE oposicion_id=1 AND ley_id=20;  -- LBRL (3 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=19;  -- LOCE (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=26;  -- LOPJ (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=18;  -- LGOB (1 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=15;  -- LODP (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=17;  -- LOTC (1 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 9 WHERE oposicion_id=1 AND ley_id=34;  -- TFUE (13 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 3 WHERE oposicion_id=1 AND ley_id=33;  -- TUE (5 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 2 WHERE oposicion_id=1 AND ley_id=51;  -- LASEE (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 2 WHERE oposicion_id=1 AND ley_id=73;  -- LO4000 (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 2 WHERE oposicion_id=1 AND ley_id=75;  -- LTRANS (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 2 WHERE oposicion_id=1 AND ley_id=22;  -- LOPD (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=77;  -- LGUM (1 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=21;  -- LTBG (1 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=27;  -- LGSS (4 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 6 WHERE oposicion_id=1 AND ley_id=4;  -- LPAC (13 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 4 WHERE oposicion_id=1 AND ley_id=12;  -- LCSP (8 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 4 WHERE oposicion_id=1 AND ley_id=7;  -- LRJSP (7 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 2 WHERE oposicion_id=1 AND ley_id=39;  -- LEF (3 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=40;  -- LPAP (1 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=57;  -- CC (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=38;  -- LGS (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=37;  -- LJCA (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 13 WHERE oposicion_id=1 AND ley_id=8;  -- TREBEP (17 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 2 WHERE oposicion_id=1 AND ley_id=42;  -- RIRS (3 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 2 WHERE oposicion_id=1 AND ley_id=69;  -- LAEPD (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 2 WHERE oposicion_id=1 AND ley_id=43;  -- MUFACE (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 2 WHERE oposicion_id=1 AND ley_id=44;  -- LMRFP (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 11 WHERE oposicion_id=1 AND ley_id=9;  -- LGP (17 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=48;  -- LOTCU (1 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=23;  -- LOEPSF (2 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=31;  -- LGT (1 en examen)
UPDATE normas.oposicion_leyes SET preguntas_simulacro = 1 WHERE oposicion_id=1 AND ley_id=29;  -- LTPP (2 en examen)

-- ── Verificación ──
-- Debe dar 100, y NINGÚN bloque a 0
SELECT bloque, SUM(preguntas_simulacro) AS peso
FROM normas.oposicion_leyes WHERE oposicion_id = 1 AND NOT excluir_test
GROUP BY bloque ORDER BY bloque;

SELECT SUM(preguntas_simulacro) AS total_debe_ser_100
FROM normas.oposicion_leyes WHERE oposicion_id = 1;
