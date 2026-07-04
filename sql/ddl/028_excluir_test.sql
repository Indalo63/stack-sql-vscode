-- ============================================================
-- Migración 028: Columna excluir_test en oposicion_leyes
-- Marca documentos de referencia que no generan preguntas de examen
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

ALTER TABLE normas.oposicion_leyes
    ADD COLUMN IF NOT EXISTS excluir_test BOOLEAN NOT NULL DEFAULT FALSE;

-- GACE_NORM: bases de la convocatoria, solo para Q&A
UPDATE normas.oposicion_leyes ol
SET excluir_test = TRUE
FROM normas.oposiciones o
WHERE ol.oposicion_id = o.oposicion_id
  AND o.codigo  = 'GACE'
  AND ol.ley_id = 14;

-- Verificación
SELECT l.codigo, ol.bloque, ol.excluir_test
FROM normas.oposicion_leyes ol
JOIN normas.oposiciones o ON o.oposicion_id = ol.oposicion_id
JOIN normas.leyes l       ON l.ley_id       = ol.ley_id
WHERE o.codigo = 'GACE' AND ol.excluir_test = TRUE;
