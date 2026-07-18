-- ============================================================
-- Migración 053: rastrear content_hash y fecha_actualizacion de normas.leyes
--
-- EL PROBLEMA QUE RESUELVE
-- Estas dos columnas YA EXISTEN en Supabase (las usa scripts/sync_boe.py
-- para detectar cambios del BOE en leyes ya cargadas), pero no las creó
-- ningún fichero de sql/ddl/: alguien las añadió a mano desde el SQL Editor
-- de Supabase sin dejar migración. Se descubrió al reconstruir el esquema
-- en un Postgres local (18/07/2026): la migración 020 y siguientes no
-- fallaron por esto (son columnas nuevas, no dependencias), pero el
-- historial de sql/ddl/ quedaba incompleto frente al estado real.
--
-- Es IF NOT EXISTS a propósito: en Supabase no cambia nada (ya existen);
-- en cualquier Postgres nuevo (local u otra instalación) las crea.
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

ALTER TABLE normas.leyes ADD COLUMN IF NOT EXISTS content_hash TEXT;
ALTER TABLE normas.leyes ADD COLUMN IF NOT EXISTS fecha_actualizacion TIMESTAMP;

COMMENT ON COLUMN normas.leyes.content_hash IS
    'Hash del contenido descargado del BOE, usado por sync_boe.py para detectar cambios.';
COMMENT ON COLUMN normas.leyes.fecha_actualizacion IS
    'Última vez que sync_boe.py comprobó/actualizó esta ley contra el BOE.';

-- Verificación
SELECT column_name FROM information_schema.columns
WHERE table_schema = 'normas' AND table_name = 'leyes'
AND column_name IN ('content_hash', 'fecha_actualizacion');
