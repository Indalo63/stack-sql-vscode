-- ============================================================
-- Migración 051: práctica intercalada (pares de leyes confundibles)
--
-- EL PROBLEMA
-- Hoy el repaso es **en bloque**: una tanda entera de LPAC, luego otra entera de
-- LRJSP. Y la práctica en bloque produce una **ilusión de fluidez**: mientras
-- machacas LPAC tienes el esquema de LPAC ya cargado, así que aciertas — y
-- concluyes que te lo sabes. El día del examen las preguntas vienen **mezcladas**,
-- y ahí resulta que no distingues **qué norma aplica a qué**.
--
-- Eso es justo lo que el tribunal explota: el plazo de la LPAC contra el de la
-- LRJSP, el órgano de una contra el de la otra. Practicarlas por separado
-- **no entrena esa distinción**. Solo entrena a responder cuando ya te han dicho
-- de qué ley va.
--
-- DE DÓNDE SALEN LOS PARES (no se inventan: se DERIVAN de la BD)
-- Dos leyes son confundibles si el **programa oficial las estudia juntas**. Eso
-- ya está en `normas.epigrafe_leyes` (qué leyes toca cada tema): el solapamiento
-- de temas entre dos leyes es la medida.
--
-- Se usa **Jaccard** (temas compartidos / temas totales de las dos), no el conteo
-- bruto, porque el conteo premia a las leyes **ubicuas**: la CE1978 aparece en 28
-- temas y la LRJSP en 24, así que comparten muchos con TODO — y no por eso se
-- confunden con todo. Jaccard lo corrige.
--
-- El resultado reproduce solo los pares que un opositor reconocería: LPAC/LRJSP
-- (0,75), ley y su reglamento (LEF/RLEF, LGS/RLGS), TUE/TFUE, TREBEP/LMRFP.
--
-- ⚠️ AVISO PEDAGÓGICO IMPORTANTE (y contraintuitivo)
-- Intercalar **empeora el rendimiento mientras se practica** y lo **mejora en el
-- examen**. Es una "dificultad deseable": se falla más, se aprende más. Dos
-- consecuencias de diseño que NO son opcionales:
--   1. **No se le sirve a un principiante en esa materia.** Intercalar antes de
--      tener una base perjudica la adquisición inicial: es ruido y frustración.
--      Por eso `min_vistas_intercalada` exige un mínimo en AMBAS leyes del par.
--   2. **Hay que avisar al alumno de que va a fallar más**, o creerá que la app
--      ha empeorado y volverá al repaso en bloque, que es el que le engaña.
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS normas.pares_confundibles (
    oposicion_id      INTEGER NOT NULL REFERENCES normas.oposiciones(oposicion_id) ON DELETE CASCADE,
    ley_a             INTEGER NOT NULL REFERENCES normas.leyes(ley_id) ON DELETE CASCADE,
    ley_b             INTEGER NOT NULL REFERENCES normas.leyes(ley_id) ON DELETE CASCADE,
    temas_compartidos INTEGER NOT NULL,
    fuerza            NUMERIC(4,3) NOT NULL,     -- Jaccard: 0.000 .. 1.000
    origen            VARCHAR(12) NOT NULL DEFAULT 'programa',
    calculado_en      TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (oposicion_id, ley_a, ley_b),
    -- Normaliza el par: siempre (menor, mayor). Sin esto habría duplicados (A,B) y (B,A).
    CONSTRAINT pares_orden_check  CHECK (ley_a < ley_b),
    CONSTRAINT pares_origen_check CHECK (origen IN ('programa', 'empirico'))
);

COMMENT ON TABLE normas.pares_confundibles IS
    'Pares de leyes que el programa oficial estudia juntas y que, por tanto, el alumno confunde. Derivados de normas.epigrafe_leyes (solapamiento de temas), NO escritos a mano. Alimentan la práctica intercalada, que es lo que entrena la DISCRIMINACIÓN entre normas parecidas — justo lo que el examen explota.';
COMMENT ON COLUMN normas.pares_confundibles.fuerza IS
    'Índice de Jaccard sobre los temas del programa: temas_compartidos / (temas de A + temas de B − compartidos). Se usa Jaccard y no el conteo bruto porque el conteo premia a las leyes ubicuas (la CE1978 está en 28 temas: comparte con todo, y no se confunde con todo).';
COMMENT ON COLUMN normas.pares_confundibles.origen IS
    'programa = derivado del temario oficial (lo que hay hoy). empirico = derivado de los fallos reales de los alumnos (requiere escala; reservado).';

CREATE INDEX IF NOT EXISTS idx_pares_fuerza
    ON normas.pares_confundibles (oposicion_id, fuerza DESC);

-- Preguntas que el alumno debe haber visto YA de CADA una de las dos leyes antes
-- de que se le ofrezca intercalarlas. Intercalar sin base perjudica: es la parte
-- contraintuitiva de la evidencia, y por eso el umbral vive en BD.
ALTER TABLE normas.parametros_aprendizaje
    ADD COLUMN IF NOT EXISTS min_vistas_intercalada INTEGER NOT NULL DEFAULT 5;

COMMENT ON COLUMN normas.parametros_aprendizaje.min_vistas_intercalada IS
    'Preguntas vistas de CADA ley del par antes de ofrecer la práctica intercalada. Intercalar antes de tener base NO ayuda: perjudica la adquisición inicial. No es un umbral de conveniencia, es una condición para que la técnica funcione.';

-- ── Verificación ──
SELECT la.codigo, lb.codigo, p.temas_compartidos, p.fuerza
FROM normas.pares_confundibles p
JOIN normas.leyes la ON la.ley_id = p.ley_a
JOIN normas.leyes lb ON lb.ley_id = p.ley_b
ORDER BY p.fuerza DESC, p.temas_compartidos DESC
LIMIT 15;
