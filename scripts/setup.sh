#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="$(dirname "$0")/../docker/docker-compose.yml"
DDL_FILE="$(dirname "$0")/../sql/ddl/001_init_schema.sql"
DML_FILE="$(dirname "$0")/../sql/dml/001_seed_sales.sql"

PG_CONTAINER="stack-sql-postgres"
PG_USER="postgres"
PG_DB="stack_db"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[OK]${NC}  $1"; }
warn()    { echo -e "${YELLOW}[--]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo "=== Stack SQL – Setup ==="
echo ""

# 1. Verificar que Docker está activo
warn "Verificando Docker..."
if ! docker info > /dev/null 2>&1; then
    error "Docker no está en marcha. Arráncalo antes de continuar."
fi
info "Docker activo."

# 2. Levantar el contenedor
warn "Levantando contenedor PostgreSQL..."
docker compose -f "$COMPOSE_FILE" up -d
info "Contenedor iniciado."

# 3. Esperar a que PostgreSQL esté listo
warn "Esperando a que PostgreSQL esté listo..."
MAX_TRIES=30
COUNT=0
until docker exec "$PG_CONTAINER" pg_isready -U "$PG_USER" -d "$PG_DB" > /dev/null 2>&1; do
    COUNT=$((COUNT + 1))
    if [ "$COUNT" -ge "$MAX_TRIES" ]; then
        error "PostgreSQL no respondió tras ${MAX_TRIES} intentos. Revisa los logs con: docker logs ${PG_CONTAINER}"
    fi
    sleep 1
done
info "PostgreSQL listo."

# 4. Cargar DDL si el esquema no existe
warn "Comprobando esquema sales..."
SCHEMA_EXISTS=$(docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -tAc \
    "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'sales';")

if [ "$SCHEMA_EXISTS" = "0" ]; then
    warn "Esquema no encontrado. Cargando DDL..."
    docker exec -i "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" < "$DDL_FILE"
    info "Esquema sales creado."
else
    info "Esquema sales ya existe. Se omite DDL."
fi

# 5. Cargar DML si no hay datos
warn "Comprobando datos de ejemplo..."
ROW_COUNT=$(docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -tAc \
    "SELECT COUNT(*) FROM sales.customers;" 2>/dev/null || echo "0")

if [ "$ROW_COUNT" = "0" ]; then
    warn "Sin datos. Cargando DML de ejemplo..."
    docker exec -i "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" < "$DML_FILE"
    info "Datos de ejemplo cargados."
else
    info "Ya existen ${ROW_COUNT} clientes. Se omite DML."
fi

# 6. Verificación final
warn "Verificando conexión final..."
RESULT=$(docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -tAc \
    "SELECT COUNT(*) FROM sales.customers;")
info "Conexión verificada. Clientes en BD: ${RESULT}."

echo ""
echo "=== Entorno listo ==="
echo ""
echo "  Conectar con psql:  docker exec -it ${PG_CONTAINER} psql -U ${PG_USER} -d ${PG_DB}"
echo "  Parar el entorno:   make stop"
echo ""
