 Stack SQL + VS Code + PostgreSQL + Claude Code

Este documento recoge la guía paso a paso para configurar un entorno de trabajo SQL con:

- Windows + WSL2 (Ubuntu)
Estado: COMPLETADO (a falta de seguir refinando las instrucciones en claude.ai).- VS Code
- Git
- PostgreSQL en Docker (por configurar)
- Extensión PostgreSQL para VS Code (por configurar)
- Claude Code en VS Code (por configurar)
- SQL Crack para visualización de SQL (por configurar)

## Paso 1 – Git en WSL2

- Git instalado en WSL2.
- Configuración global realizada:
  - user.name: Indalecio Plaza
  - user.email: [TU_CORREO]

Estado: COMPLETADO.

## Paso 2 – Carpeta base del proyecto

- Ruta base de proyectos: ~/dev
- Carpeta del proyecto de stack: ~/dev/stack-sql-vscode
- Repo Git inicializado en esa carpeta.
- Primer commit con este documento y CLAUDE.md.

Estado: COMPLETADO.

## Paso 3 – Integración con Claude

- Archivo CLAUDE.md creado en la raíz del proyecto.
- CLAUDE.md describe:
  - Quién soy.
  - Objetivo del proyecto.
  - Forma de trabajo paso a paso.
  - Entorno asumido.
- (Opcional) Proyecto creado en claude.ai para este stack.

Estado: COMPLETADO (a falta de seguir refinando las instrucciones en claude.ai).

## Paso 4 – Estructura base para SQL y documentación de la BD

- Carpetas creadas:
  - sql/ddl
  - sql/dml
  - sql/queries
  - sql/snippets
  - sql/tests
- Estructura de documentación creada:
  - docs/database/
  - docs/database/tables/
- Documentos iniciales:
  - docs/database/schema-summary.md (plantilla inicial)
  - docs/database/naming-conventions.md (convenciones de nombres)

Estado: COMPLETADO.

## Paso 5 – PostgreSQL en Docker (esquema genérico clientes/pedidos)

- Carpeta docker/ creada.
- Archivo docker/docker-compose.yml creado con servicio:
  - imagen: postgres:16
  - contenedor: stack-sql-postgres
  - usuario: stack_user
  - base de datos: stack_db
  - volumen postgres_data para persistencia.
  - montaje de sql/ddl en /docker-entrypoint-initdb.d.
- Script de inicialización:
  - sql/ddl/001_init_schema.sql con esquema sales y tablas:
    - sales.customers
    - sales.orders
- Contenedor levantado con:
  - docker compose up -d
- Verificación realizada con:
  - docker exec -it stack-sql-postgres psql -U stack_user -d stack_db
  - \dn
  - \dt sales.*

Estado: COMPLETADO.

## Paso 6 – Documentación del esquema y consultas básicas

- Actualizado docs/database/schema-summary.md con:
  - Esquema sales.
  - Tablas sales.customers y sales.orders.
  - Relaciones principales.
- Creado sql/queries/basic_examples.sql con consultas muy simples:
  - SELECT * FROM sales.customers;
  - SELECT * FROM sales.orders;
  - Join básico entre customers y orders.
- Nuevas consultas de ejemplo:
  - sql/queries/customers_with_multiple_orders.sql
- Scripts DML de ejemplo:
  - sql/dml/... (seeds para el esquema sales)


Estado: COMPLETADO.

