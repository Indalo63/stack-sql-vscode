-- ============================================================
-- Migración 040: usuario de base de datos con permisos mínimos para la app
--
-- Motivo (auditoría de seguridad, 12/07/2026): la app conectaba como `postgres`,
-- que puede BORRAR TABLAS (DDL) y se salta el Row Level Security
-- (rolbypassrls = TRUE). Un bug o una futura inyección SQL podían destruir el
-- esquema entero.
--
-- Se comprobó qué necesita realmente la app: SELECT en todo `normas`, INSERT y
-- UPDATE en unas pocas tablas, y NADA MÁS. En concreto:
--   - NO hace ningún DELETE (rechazar una pregunta ya es un borrado lógico, 039)
--   - NO hace ningún CREATE / ALTER / DROP
-- Así que el rol no recibe ni DELETE, ni TRUNCATE, ni permisos de DDL.
--
-- IMPORTANTE — las migraciones NO se ejecutan con este usuario: se siguen
-- aplicando como `postgres` desde el SQL Editor de Supabase. Este rol es solo
-- para que la aplicación se conecte en el día a día.
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- Antes de ejecutar, sustituye la contraseña de abajo por una generada al azar
-- (y guárdala en los secrets; nunca en este repositorio).
-- ============================================================

-- ── 1. El rol ────────────────────────────────────────────────────────────────
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_asistente') THEN
        CREATE ROLE app_asistente LOGIN PASSWORD 'CAMBIAR_POR_UNA_CONTRASENA_ALEATORIA';
    END IF;
END
$$;

-- Sin capacidad de crear bases ni roles.
--
-- Nota: NO se ponen aquí NOSUPERUSER ni NOBYPASSRLS aunque sean lo deseado. En
-- Supabase el usuario `postgres` NO es superusuario real, y esas dos cláusulas
-- exigen serlo (aunque no cambien nada): la sentencia fallaría con "permission
-- denied to alter role". Un rol recién creado ya nace SIN superusuario y SIN
-- bypassrls, que es justo lo que queremos; la verificación del final lo comprueba.
ALTER ROLE app_asistente NOCREATEDB NOCREATEROLE;

-- ── 2. Acceso a los esquemas (sin poder crear objetos en ellos) ───────────────
GRANT USAGE ON SCHEMA normas TO app_asistente;
GRANT USAGE ON SCHEMA public TO app_asistente;   -- pgvector vive aquí
REVOKE CREATE ON SCHEMA normas, public FROM app_asistente;

-- ── 3. Lectura de todo el esquema ────────────────────────────────────────────
GRANT SELECT ON ALL TABLES IN SCHEMA normas TO app_asistente;
ALTER DEFAULT PRIVILEGES IN SCHEMA normas
    GRANT SELECT ON TABLES TO app_asistente;      -- también las tablas futuras

-- ── 4. Escritura SOLO donde la app la necesita ───────────────────────────────
-- (verificado buscando INSERT/UPDATE en app/ y scripts/build_test_bank.py)
GRANT INSERT, UPDATE ON
    normas.preguntas_test,                 -- generar (INSERT) y aprobar/descartar (UPDATE)
    normas.editores,                       -- alta, revocación, cambio de rol
    normas.progreso_usuario,               -- repaso SM-2 del alumno (upsert)
    normas.plan_estudio,                   -- progreso por tema (upsert)
    normas.historial_simulacros,           -- notas de simulacro
    normas.simulacros_academia,            -- generar y autorizar
    normas.simulacro_academia_preguntas    -- preguntas fijas del simulacro
TO app_asistente;

-- Secuencias de los ids autonuméricos de esas tablas
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA normas TO app_asistente;
ALTER DEFAULT PRIVILEGES IN SCHEMA normas
    GRANT USAGE, SELECT ON SEQUENCES TO app_asistente;

-- ── 5. Lo que NO se concede (a propósito) ────────────────────────────────────
--   DELETE     → la app no borra nada; el descarte de preguntas es lógico (039)
--   TRUNCATE   → ídem
--   CREATE/DDL → la app no crea ni altera tablas; eso son migraciones (postgres)
-- Blindaje explícito por si algún GRANT amplio se colara en el futuro:
REVOKE DELETE, TRUNCATE ON ALL TABLES IN SCHEMA normas FROM app_asistente;

-- ── Verificación ──
-- Debe devolver: superusuario=f, salta_rls=f, puede_ddl=f
SELECT rolname,
       rolsuper      AS superusuario,
       rolbypassrls  AS salta_rls,
       has_schema_privilege('app_asistente', 'normas', 'CREATE') AS puede_ddl
FROM pg_roles WHERE rolname = 'app_asistente';

-- Debe devolver 0 filas (ninguna tabla con permiso de borrado)
SELECT table_name, privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'app_asistente'
  AND privilege_type IN ('DELETE', 'TRUNCATE');
