-- ============================================================
-- Migración 046: perfil del alumno (experiencia previa)
--
-- POR QUÉ (análisis del 12/07/2026):
-- La prueba de nivel se ofrecía por defecto a todo alumno nuevo. Pero su valor
-- pedagógico es **exactamente el inverso** de lo que asumía ese diseño:
--
--   · PRINCIPIANTE (primera oposición): la prueba es INÚTIL y probablemente
--     dañina. Un test diagnostica cuando hay algo que diferenciar; si el alumno
--     está a cero en todo, no hay señal, solo el ~25% del azar. "No sabes nada"
--     no es un diagnóstico. Y arrancar con un fracaso rotundo daña la
--     autoeficacia justo cuando es más frágil. Además el motor NO la necesita:
--     la fase "inicio" del mix ya arranca de cero.
--
--   · VIENE DE OTRA OPOSICIÓN: aquí la prueba vale mucho. Tiene conocimiento
--     previo REAL y DESIGUAL (suele dominar Derecho Administrativo, común a casi
--     todas, y no saber nada de UE o Gestión Financiera). Eso es justo lo que un
--     diagnóstico debe encontrar. Sin la prueba, el SM-2 tardaría semanas en
--     descubrirlo sirviéndole preguntas que ya domina -> aburrimiento y abandono.
--
-- DECISIÓN (usuario, 12/07/2026):
--   · Principiante  -> NO se le hace la prueba. Se le da un PLAN DE PARTIDA
--     basado en el peso oficial del examen y en la frecuencia real de cada tema
--     (Radar del Tribunal). Conserva el gancho comercial ("tu plan personalizado")
--     sin el daño de la nota humillante. Puede hacerla más tarde si quiere.
--   · Viene de otra -> prueba MUY recomendada, pero no obligatoria.
--
-- Se pregunta UNA sola cosa al registrarse. Sin este dato es imposible distinguir
-- los dos perfiles (hoy no se guarda nada del alumno).
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS normas.perfil_alumno (
    user_id           TEXT PRIMARY KEY,          -- UUID de Supabase Auth
    experiencia       VARCHAR(20) NOT NULL,      -- 'primera' | 'otras_oposiciones'
    prueba_ofrecida   BOOLEAN NOT NULL DEFAULT FALSE,  -- ya se le ofreció (para no insistir)
    creado_en         TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT perfil_alumno_experiencia_check
        CHECK (experiencia IN ('primera', 'otras_oposiciones'))
);

COMMENT ON TABLE normas.perfil_alumno IS
    'Perfil del alumno, preguntado al registrarse. Decide el recorrido inicial: al principiante NO se le hace la prueba de nivel (mediría ruido y le desmotivaría), al que viene de otra oposición sí se le recomienda con fuerza (tiene conocimiento previo desigual, que es justo lo que la prueba detecta).';
COMMENT ON COLUMN normas.perfil_alumno.experiencia IS
    'primera = primera oposición a la que se presenta. otras_oposiciones = ya se ha presentado a otras (tiene base previa, normalmente desigual por bloques).';

-- ── Verificación ──
SELECT experiencia, COUNT(*) FROM normas.perfil_alumno GROUP BY experiencia;
