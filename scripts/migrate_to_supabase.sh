#!/usr/bin/env bash
# migrate_to_supabase.sh
#
# Migra el schema y los datos desde el PostgreSQL local (Docker) a Supabase.
#
# Requisitos previos:
#   - Docker en ejecución con el contenedor PostgreSQL del proyecto
#   - psql instalado en WSL2: sudo apt install postgresql-client
#   - Credenciales de Supabase listas (ver docs/deploy-supabase-streamlit.md)
#
# Uso:
#   chmod +x scripts/migrate_to_supabase.sh
#   SUPABASE_URL="postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres" \
#     bash scripts/migrate_to_supabase.sh

set -euo pipefail

# ── Configuración local (Docker) ──────────────────────────────────────────────
LOCAL_HOST="localhost"
LOCAL_PORT="5432"
LOCAL_DB="stack_db"
LOCAL_USER="postgres"
LOCAL_PASSWORD="postgres"

LOCAL_URL="postgresql://${LOCAL_USER}:${LOCAL_PASSWORD}@${LOCAL_HOST}:${LOCAL_PORT}/${LOCAL_DB}"

# ── Supabase ──────────────────────────────────────────────────────────────────
if [[ -z "${SUPABASE_URL:-}" ]]; then
  echo "ERROR: define SUPABASE_URL antes de ejecutar este script."
  echo "  export SUPABASE_URL='postgresql://postgres:<pass>@db.<ref>.supabase.co:5432/postgres'"
  exit 1
fi

DUMP_FILE="/tmp/normas_dump_$(date +%Y%m%d_%H%M%S).sql"

echo "=== Paso 1: volcado del schema + datos desde Docker local ==="
PGPASSWORD="${LOCAL_PASSWORD}" pg_dump \
  --host="${LOCAL_HOST}" \
  --port="${LOCAL_PORT}" \
  --username="${LOCAL_USER}" \
  --schema="normas" \
  --no-owner \
  --no-acl \
  --format=plain \
  "${LOCAL_DB}" > "${DUMP_FILE}"

echo "  Volcado guardado en: ${DUMP_FILE}"
echo "  Tamaño: $(du -sh "${DUMP_FILE}" | cut -f1)"

echo ""
echo "=== Paso 2: habilitando extensión vector en Supabase ==="
psql "${SUPABASE_URL}" -c "CREATE EXTENSION IF NOT EXISTS vector;" || true

echo ""
echo "=== Paso 3: cargando schema y datos en Supabase ==="
psql "${SUPABASE_URL}" < "${DUMP_FILE}"

echo ""
echo "=== Paso 4: verificación ==="
psql "${SUPABASE_URL}" -c "
SELECT l.codigo, l.nombre_corto, COUNT(a.articulo_id) AS articulos
FROM normas.leyes l
LEFT JOIN normas.articulos a USING (ley_id)
GROUP BY l.ley_id, l.codigo, l.nombre_corto
ORDER BY l.ley_id;
"

echo ""
echo "Migración completada. Actualiza los valores en .streamlit/secrets.toml"
echo "con las credenciales de Supabase (DB_HOST, DB_PASSWORD, etc.)."
