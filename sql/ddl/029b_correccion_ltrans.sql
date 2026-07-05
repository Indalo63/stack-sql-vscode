-- ============================================================
-- Corrección 029b: nombre_corto incorrecto en LTRANS
-- LTRANS = Ley 4/2023 Trans e Igualdad LGTBI (108 artículos)
-- no "Ley 16/1987 Transportes Terrestres" como se escribió por error
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

UPDATE normas.leyes
SET nombre_corto = 'LO 4/2023 — Trans e Igualdad LGTBI'
WHERE codigo = 'LTRANS';

-- Verificación
SELECT codigo, nombre_corto FROM normas.leyes WHERE codigo = 'LTRANS';
