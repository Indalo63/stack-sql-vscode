# Current State

## Purpose of this document

Este documento describe el estado actual real del proyecto `stack-sql-vscode` en el momento de su última actualización válida.

Su función es permitir retomar el trabajo técnico sin depender de la memoria de sesiones anteriores, dejando claro qué existe ya, qué está verificado y qué queda pendiente de forma inmediata.

## Project identity

`stack-sql-vscode` es un proyecto de aprendizaje y trabajo práctico orientado a SQL con PostgreSQL, VS Code, Docker y Claude Code.

El objetivo actual del proyecto es construir una base técnica y documental sólida para:

- practicar SQL de forma estructurada
- usar Claude Code como copiloto técnico, profesor y apoyo de arquitectura
- preparar el terreno para una futura integración con `pgvector`, `n8n` y flujos de tipo RAG

## Working environment

Entorno de trabajo actual:

- sistema anfitrión: Windows
- entorno de desarrollo principal: WSL2 con Ubuntu
- editor: VS Code
- control de versiones: Git
- contenedores: Docker
- base de datos principal: PostgreSQL
- soporte vectorial: `pgvector`
- asistente de trabajo: Claude Code

La ruta base de trabajo del proyecto es:

```text
~/dev/stack-sql-vscode
```

## Repository structure

Estructura relevante del repositorio:

- `docs/`
  - documentación funcional y de proyecto
- `docs/database/`
  - documentación del esquema y estructura de datos
- `docs/sql/`
  - guía de estilo SQL y recetas de prompts
- `docs/project/`
  - contexto general del proyecto, arquitectura, bitácora, decisiones y próximos pasos
- `sql/`
  - scripts SQL del proyecto
- `sql/ddl/`
  - scripts de definición de esquema
- `sql/dml/`
  - datos de ejemplo y scripts de carga
- `sql/queries/`
  - consultas SQL de práctica y ejemplos
- `docker/`
  - infraestructura local basada en Docker
- `CLAUDE.md`
  - contexto base del proyecto para Claude

## Installed and configured tools

Herramientas que forman parte del estado actual del proyecto:

- Git en WSL2
- VS Code como editor principal
- Docker para ejecutar PostgreSQL localmente
- PostgreSQL dentro de contenedor Docker
- extensión `pgvector` disponible a través de la imagen usada
- documentación SQL base ya creada
- recetas de prompts para Claude Code ya definidas

Herramientas previstas pero no consideradas todavía como parte cerrada del estado operativo:

- `n8n` self-hosted en Docker
- automatismos RAG completos
- tablas vectoriales de uso real más allá de la verificación de instalación

## PostgreSQL and Docker status

Estado actual de la infraestructura local de base de datos:

- archivo de infraestructura principal: `docker/docker-compose.yml`
- versión de compose declarada: `3.9`
- servicio: `postgres`
- imagen actual: `pgvector/pgvector:pg16`
- nombre del contenedor: `stack-sql-postgres`
- usuario de PostgreSQL: `postgres`
- contraseña de PostgreSQL: `postgres`
- base de datos principal: `stack_db`
- puerto expuesto: `5432:5432`
- volumen local de datos: `./data/postgres_pgvector:/var/lib/postgresql/data`

Esto significa que PostgreSQL ya no está definido como `postgres:16` genérico, sino como una imagen preparada para trabajar con `pgvector`.

## pgvector status

El proyecto ha evolucionado desde una instalación base de PostgreSQL en Docker hacia una instalación con soporte vectorial integrado.

Estado verificado:

- imagen en uso: `pgvector/pgvector:pg16`
- extensión activada en la base: `vector`
- verificación realizada con `\dx`
- versión observada de la extensión: `0.8.2`
- esquema donde aparece instalada: `public`

Interpretación práctica:

- PostgreSQL está preparado para almacenar vectores
- el proyecto puede evolucionar hacia búsquedas por similitud
- ya existe base técnica para trabajar con embeddings y futuras automatizaciones RAG

## SQL documentation status

La documentación SQL existente y ya disponible en el proyecto incluye:

- `docs/database/schema-summary.md`
  - resumen del esquema de ejemplo `sales`
- `docs/sql/style-guide.md`
  - reglas de estilo SQL para el proyecto y para el SQL generado por Claude Code
- `docs/sql/prompt-recipes.md`
  - recetas reutilizables para pedir a Claude generación, explicación, refactorización, optimización y ejercicios SQL

Esta documentación constituye la base mínima para trabajar SQL en el proyecto con consistencia técnica y pedagógica.

## Query and practice files status

Estado actual conocido de los archivos SQL de práctica:

- existe un script de inicialización de esquema:
  - `sql/ddl/001_init_schema.sql`
- existe documentación del esquema de ejemplo `sales`
- existen consultas básicas en:
  - `sql/queries/basic_examples.sql`
- existe al menos una consulta adicional de práctica:
  - `sql/queries/customers_with_multiple_orders.sql`
- existe estructura preparada para DDL, DML, queries, snippets y tests

El dominio funcional de práctica sigue siendo un modelo simple de clientes y pedidos:

- `sales.customers`
- `sales.orders`

## Claude-related project context

El proyecto está preparado para trabajar con Claude de forma estructurada.

Piezas clave ya existentes:

- `CLAUDE.md` en la raíz del proyecto
- `docs/sql/style-guide.md`
- `docs/sql/prompt-recipes.md`
- `docs/database/schema-summary.md`
- `docs/project/README.md`
- este archivo `docs/project/01-current-state.md`

El papel esperado de Claude en este proyecto es mixto:

- copiloto técnico
- profesor para explicación de SQL
- apoyo de arquitectura y documentación

## Verified current capabilities

Capacidades que pueden considerarse verificadas en el estado actual:

- navegar y mantener un repositorio Git en WSL2
- editar el proyecto en VS Code
- ejecutar PostgreSQL en Docker localmente
- conectarse al contenedor `stack-sql-postgres`
- trabajar contra la base `stack_db`
- usar la extensión `vector` en PostgreSQL
- documentar el esquema `sales`
- generar y revisar SQL con apoyo de Claude Code
- aplicar una guía de estilo SQL consistente
- usar recetas de prompts reutilizables para tareas SQL

## Immediate pending work

Trabajo inmediato recomendado a partir del estado actual:

1. completar la documentación de `docs/project/`
2. consolidar la bitácora cronológica real del proyecto
3. reflejar explícitamente en la documentación la migración a `pgvector`
4. definir y crear una tabla vectorial realista, por ejemplo `ai_document_chunks`
5. probar una consulta vectorial sencilla con datos de ejemplo
6. solo después de validar lo anterior, instalar `n8n` en Docker y conectarlo a `stack_db`

## Risks or open points

Puntos abiertos o sensibles en este momento:

- parte de la documentación antigua todavía refleja una fase anterior del proyecto y debe actualizarse
- la evolución hacia `pgvector` aún no está consolidada en todos los documentos
- `n8n` todavía no forma parte del stack operativo actual
- aún no existe una tabla vectorial de trabajo documentada como parte estable del proyecto
- todavía queda por separar claramente lo que está verificado de lo que es siguiente paso o hipótesis

Este documento debe actualizarse cada vez que cambie el estado operativo real del proyecto.