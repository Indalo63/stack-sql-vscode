-- ============================================================
-- Migración 036: normas.editores (lista blanca de acceso a Gestión banco de preguntas)
--
-- Motivo: hasta ahora la app NO validaba QUÉ cuenta de Google entraba: bastaba
-- con completar el OAuth para obtener acceso completo de gestión (generar,
-- aprobar y borrar preguntas; autorizar simulacros). El único control era el
-- modo "Testing" de la pantalla de consentimiento de Google Cloud — externo al
-- código y fácil de anular por accidente al publicarla.
--
-- La lista vive en BD (no en código ni en secrets) para poder dar de alta o
-- revocar a un editor sin redesplegar, y para escalar al modelo B2B (cada
-- academia con sus propios editores).
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS normas.editores (
    email      VARCHAR(150) PRIMARY KEY,        -- email de la cuenta Google
    nombre     VARCHAR(150),
    academia   VARCHAR(150),                    -- reservado para el modelo B2B (multi-academia)
    activo     BOOLEAN     NOT NULL DEFAULT TRUE,
    creado_en  TIMESTAMP   NOT NULL DEFAULT NOW(),
    creado_por VARCHAR(150)                     -- quién lo dio de alta
);

COMMENT ON TABLE normas.editores IS
    'Lista blanca de cuentas Google con acceso al perfil "Gestión banco de preguntas". Una sesión Google válida NO basta: el email debe existir aquí con activo=TRUE. Para revocar el acceso, poner activo=FALSE (preferible a borrar: conserva la trazabilidad de preguntas_test.revisado_por).';
COMMENT ON COLUMN normas.editores.activo IS
    'FALSE revoca el acceso sin borrar la fila (mantiene el histórico de revisiones).';
COMMENT ON COLUMN normas.editores.academia IS
    'Reservado: en el modelo B2B, a qué academia pertenece el editor. NULL = plataforma.';

-- ── Bootstrap: sin esta fila, NADIE puede entrar en Gestión banco de preguntas ──
INSERT INTO normas.editores (email, nombre, activo, creado_por)
VALUES ('indaleciopf@gmail.com', 'Indalecio Plaza', TRUE, 'migracion_036')
ON CONFLICT (email) DO NOTHING;

-- ── Verificación ──
SELECT email, nombre, activo, creado_en FROM normas.editores ORDER BY creado_en;
