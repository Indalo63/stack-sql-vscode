.DEFAULT_GOAL := help

COMPOSE_FILE := docker/docker-compose.yml
PG_CONTAINER := stack-sql-postgres
PG_USER      := postgres
PG_DB        := stack_db

help:
	@echo ""
	@echo "Comandos disponibles:"
	@echo ""
	@echo "  make setup   Levanta el entorno y carga esquema + datos de ejemplo"
	@echo "  make start   Levanta el contenedor (sin cargar esquema ni datos)"
	@echo "  make stop    Para el contenedor"
	@echo "  make reset   Destruye el entorno y lo reconstruye desde cero"
	@echo "  make psql    Abre una sesión psql interactiva"
	@echo "  make status  Muestra el estado del contenedor"
	@echo ""

setup:
	@bash scripts/setup.sh

start:
	docker compose -f $(COMPOSE_FILE) up -d

stop:
	docker compose -f $(COMPOSE_FILE) down

reset:
	docker compose -f $(COMPOSE_FILE) down -v
	sudo rm -rf docker/data/postgres_pgvector
	@bash scripts/setup.sh

psql:
	docker exec -it $(PG_CONTAINER) psql -U $(PG_USER) -d $(PG_DB)

status:
	docker compose -f $(COMPOSE_FILE) ps

.PHONY: help setup start stop reset psql status
