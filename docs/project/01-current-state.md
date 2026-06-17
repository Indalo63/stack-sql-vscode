# Current State

## Purpose of this document

Este documento describe el estado actual real del proyecto `stack-sql-vscode`.

Su función es permitir retomar el trabajo técnico sin depender de la memoria de sesiones anteriores, dejando claro qué existe, qué está verificado y cuál es el siguiente paso.

## Project identity

`stack-sql-vscode` es un proyecto técnico personal orientado a SQL con PostgreSQL, VS Code, Docker y Claude Code. Su objetivo ha evolucionado desde la práctica SQL básica hacia la construcción de una base de datos legislativa con búsqueda semántica, como base para una aplicación de Q&A jurídico.

## Working environment

- Sistema anfitrión: Windows con WSL2 (Ubuntu 24.04 LTS)
- Editor: VS Code con Claude Code
- Control de versiones: Git
- Contenedores: Docker Desktop con integración WSL2
- Base de datos: PostgreSQL 16 con pgvector
- Ruta base: `~/dev/stack-sql-vscode`

## Docker stack

| Servicio | Imagen | Puerto | Contenedor |
|---|---|---|---|
| PostgreSQL + pgvector | `pgvector/pgvector:pg16` | 5432 | `stack-sql-postgres` |
| pgAdmin 4 | `dpage/pgadmin4:latest` | 5050 | `stack-sql-pgadmin` |

- Base de datos: `stack_db` / usuario: `postgres` / contraseña: `postgres`
- pgAdmin: `indaleciopf@gmail.com` / contraseña: `postgres`
- Levantar stack: `docker compose -f docker/docker-compose.yml up -d`

## Esquemas activos en stack_db

### Esquema `sales` (práctica SQL básica)

Modelo mínimo de clientes y pedidos para practicar SQL relacional.

- `sales.customers` — clientes
- `sales.orders` — pedidos

Scripts: `sql/ddl/001_init_schema.sql`, `sql/dml/001_seed_sales.sql`

### Esquema `legislacion` (base de datos legislativa CE)

Base de datos de la Constitución Española (1978) con búsqueda semántica mediante pgvector.

**Tablas:**
- `legislacion.leyes` — metadatos de la ley
- `legislacion.titulos` — 11 títulos (Preliminar + I al X)
- `legislacion.capitulos` — 11 capítulos (Títulos I, III y VIII)
- `legislacion.secciones` — 2 secciones (Título I, Capítulo Segundo)
- `legislacion.articulos` — 185 elementos: preámbulo, 169 artículos, 15 disposiciones

**Estado:**
- Texto oficial extraído del BOE (permalink ELI)
- 185/185 embeddings generados con `text-embedding-3-small` (OpenAI, vector 1536)
- Índice HNSW operativo para búsqueda semántica por similitud coseno
- Búsqueda semántica verificada y funcionando

Scripts: `sql/ddl/002_constitucion_schema.sql`, `sql/dml/002_constitucion_seed.sql`
Documentación: `docs/database/constitucion/`

## Extensión pgvector

- Versión: `0.8.2`
- Esquema: `public`
- Verificada con `\dx` en `stack_db`

## Documentación existente

| Archivo | Contenido |
|---|---|
| `docs/database/schema-summary.md` | Resumen de ambos esquemas (sales + legislacion) |
| `docs/database/constitucion/` | Documentación completa del módulo legislativo (4 archivos) |
| `docs/sql/style-guide.md` | Guía de estilo SQL del proyecto |
| `docs/sql/prompt-recipes.md` | Recetas de prompts para Claude Code |
| `docs/project/` | Contexto, arquitectura, bitácora, decisiones y próximos pasos |

## Scripts disponibles

| Script | Propósito |
|---|---|
| `scripts/generate_embeddings.py` | Genera embeddings con OpenAI (requiere `OPENAI_API_KEY`) |
| `scripts/menu.sh` | Menú de gestión del stack |
| `scripts/setup.sh` | Setup inicial del entorno |
| `scripts/launcher.bat` | Lanzador desde Windows |

## Objetivo actual

Construir una aplicación de Q&A jurídico sobre la Constitución Española:
- la base de datos legislativa es la capa de datos
- pgvector permite búsqueda semántica para recuperar artículos relevantes
- el siguiente paso es conectar esta base con un modelo de lenguaje (Claude)

## Immediate pending work

1. Diseñar la arquitectura de la app de Q&A (capa de recuperación + capa de generación)
2. Implementar el pipeline: pregunta → embedding → búsqueda semántica → contexto → respuesta
3. Definir la interfaz (script Python, API REST, integración n8n...)
