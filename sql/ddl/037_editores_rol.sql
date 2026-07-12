-- ============================================================
-- Migración 037: normas.editores.rol (admin / editor)
--
-- Motivo: la lista blanca (036) daba a todos los editores los mismos permisos.
-- Con la nueva pantalla de gestión de editores hace falta distinguir quién
-- puede dar de alta y revocar a otros:
--   - 'admin'  → gestiona la lista de editores (además de todo lo de 'editor')
--   - 'editor' → genera y revisa preguntas, pero NO gestiona editores
--
-- Prepara además el modelo B2B: cada academia tendrá su propio admin.
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

ALTER TABLE normas.editores
    ADD COLUMN IF NOT EXISTS rol VARCHAR(20) NOT NULL DEFAULT 'editor';

-- Solo se aceptan los dos roles previstos (evita typos silenciosos)
ALTER TABLE normas.editores
    DROP CONSTRAINT IF EXISTS editores_rol_check;
ALTER TABLE normas.editores
    ADD CONSTRAINT editores_rol_check CHECK (rol IN ('admin', 'editor'));

COMMENT ON COLUMN normas.editores.rol IS
    'admin = puede gestionar la lista de editores desde la app; editor = solo genera y revisa preguntas. La app impide dejar cero admins activos (bloqueo de acceso).';

-- ── Bootstrap: el propietario pasa a admin ────────────────────────────────────
-- Sin al menos un admin, nadie podría gestionar editores desde la app.
UPDATE normas.editores
   SET rol = 'admin'
 WHERE email = 'indaleciopf@gmail.com';

-- ── Verificación ──
SELECT email, nombre, rol, activo FROM normas.editores ORDER BY rol, email;
