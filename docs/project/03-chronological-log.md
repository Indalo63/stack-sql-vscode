# Chronological Log

## Purpose of this document

Este documento registra el recorrido real del proyecto `stack-sql-vscode` paso a paso.

Su objetivo es conservar la secuencia de construcción del proyecto para que cualquier continuidad futura pueda apoyarse en un historial claro de decisiones, acciones y resultados, sin depender de la memoria de conversaciones anteriores.

## How to read this log

Esta bitácora no está organizada por fechas exactas ni por versiones del proyecto.

Está organizada por pasos reales de evolución. Cada paso resume:

- el objetivo del momento
- las acciones realizadas
- el resultado alcanzado
- el estado actual de ese bloque de trabajo

## Step 1 – Git in WSL2

### Objective

Preparar un entorno de trabajo local sólido en WSL2 con control de versiones funcional.

### Actions

- instalación y verificación de Git dentro de WSL2
- preparación del entorno Linux como base de trabajo técnico
- definición del flujo de trabajo local desde terminal y VS Code

### Result

El proyecto pasó a apoyarse en un entorno reproducible y apto para desarrollo técnico real, evitando depender del sistema Windows como espacio directo de trabajo.

### Status

Completado.

## Step 2 – Project base folder and repository

### Objective

Crear una base de proyecto clara y reutilizable para centralizar scripts, documentación y evolución futura.

### Actions

- creación de la carpeta de trabajo `~/dev/stack-sql-vscode`
- inicialización del repositorio Git
- definición de una estructura inicial para separar documentación y archivos técnicos

### Result

Quedó creada una raíz de proyecto estable desde la que organizar tanto la parte SQL como la parte documental y de infraestructura.

### Status

Completado.

## Step 3 – Claude integration

### Objective

Incorporar Claude como herramienta persistente de apoyo al desarrollo, documentación y aprendizaje.

### Actions

- creación de `CLAUDE.md` en la raíz del proyecto
- definición de Claude como copiloto técnico, profesor y apoyo de arquitectura
- orientación del proyecto hacia un uso estructurado del contexto documental

### Result

Claude quedó integrado como parte del workflow de desarrollo, no como uso aislado o improvisado.

### Status

Completado.

## Step 4 – SQL and database documentation structure

### Objective

Separar y organizar la documentación técnica relacionada con SQL y base de datos.

### Actions

- creación de carpetas específicas para documentación
- definición de una separación entre documentación de base de datos y documentación SQL
- preparación del repositorio para albergar guías, resúmenes de esquema y recetas de trabajo

### Result

El proyecto dejó de depender de archivos sueltos y pasó a tener una estructura documental coherente para datos y SQL.

### Status

Completado.

## Step 5 – PostgreSQL in Docker

### Objective

Levantar una base de datos PostgreSQL local, aislada y fácil de reproducir mediante Docker.

### Actions

- creación de configuración Docker para PostgreSQL
- definición del servicio de base de datos en `docker/docker-compose.yml`
- exposición del puerto `5432`
- arranque del contenedor para desarrollo local

### Result

PostgreSQL pasó a ejecutarse como servicio local en contenedor, convirtiéndose en la base operativa del stack técnico.

### Status

Completado.

## Step 6 – Schema and basic SQL practice files

### Objective

Disponer de un modelo relacional pequeño y útil para practicar SQL y documentar ejemplos.

### Actions

- creación del script `sql/ddl/001_init_schema.sql`
- definición del esquema `sales`
- creación del modelo base con `sales.customers` y `sales.orders`
- preparación de archivos de consultas de ejemplo

### Result

El proyecto quedó equipado con un dominio de práctica simple, suficiente para escribir consultas, explicarlas y refactorizarlas con Claude.

### Status

Completado.

## Step 7 – SQL style guide

### Objective

Establecer una convención de estilo estable para el SQL humano y el SQL generado con ayuda de Claude.

### Actions

- creación de `docs/sql/style-guide.md`
- definición de reglas sobre `snake_case`, uso de esquemas, alias, `JOIN`, CTEs y comentarios
- consolidación de un estándar de legibilidad compartido

### Result

El proyecto ganó consistencia técnica y redujo el riesgo de deriva estilística entre consultas escritas manualmente y consultas sugeridas por Claude.

### Status

Completado.

## Step 8 – Prompt recipes for Claude Code

### Objective

Estandarizar la interacción con Claude Code para tareas SQL repetibles.

### Actions

- creación de `docs/sql/prompt-recipes.md`
- diseño de recetas para:
  - generar consultas nuevas
  - explicar consultas existentes
  - refactorizar SQL complejo
  - optimizar consultas
  - crear ejercicios didácticos
- conexión explícita de estas recetas con el esquema y la guía de estilo

### Result

Quedó definido un marco práctico para trabajar con Claude Code de forma repetible, controlada y alineada con el proyecto.

### Status

Completado.

## Step 9 – SQL Crack exploration

### Objective

Explorar herramientas complementarias para entender mejor la estructura y lógica de las consultas SQL.

### Actions

- evaluación de SQL Crack como herramienta de apoyo visual y explicativo
- análisis de su posible encaje dentro del workflow del proyecto
- valoración de su utilidad como capa complementaria frente al trabajo principal con Claude y PostgreSQL

### Result

SQL Crack quedó identificado como herramienta auxiliar potencialmente útil para aprendizaje y visualización, pero no como eje principal del stack.

### Status

Explorado, no central.

## Step 10 – pgvector migration

### Objective

Preparar la arquitectura para evolucionar desde SQL relacional puro hacia capacidades vectoriales y futuros flujos RAG.

### Actions

- sustitución de una imagen PostgreSQL genérica por `pgvector/pgvector:pg16`
- actualización del servicio en `docker/docker-compose.yml`
- uso del contenedor `stack-sql-postgres`
- configuración de:
  - `POSTGRES_USER=postgres`
  - `POSTGRES_PASSWORD=postgres`
  - `POSTGRES_DB=stack_db`
- mantenimiento del puerto `5432`
- activación y verificación de la extensión `vector`
- confirmación de la disponibilidad de `pgvector` en la base de datos

### Result

El proyecto dejó de ser únicamente un stack SQL relacional y pasó a disponer de una base técnica válida para almacenamiento vectorial y búsquedas por similitud.

### Status

Completado y verificado.

## Step 11 – Current documentation reorganization

### Objective

Separar la documentación de proyecto y contexto Claude del resto de documentación SQL para mejorar continuidad y mantenimiento.

### Actions

- decisión de crear `docs/project/`
- creación de la carpeta y de los archivos numerados
- definición de un `README.md` útil para el proyecto
- redacción de `01-current-state.md`
- redacción de `02-architecture.md`
- diseño de la secuencia de documentación paso a paso

### Result

El proyecto pasó a tener una capa documental específica para contexto operativo, arquitectura, bitácora, decisiones y siguientes pasos.

### Status

En progreso, con base ya creada.

## Current checkpoint

En el momento actual, el proyecto dispone de:

- un entorno local estable en WSL2 + VS Code
- Git como base de control de cambios
- PostgreSQL ejecutándose en Docker
- soporte vectorial con `pgvector`
- un esquema SQL didáctico y documentado
- una guía de estilo SQL
- recetas de prompts para Claude Code
- una nueva capa `docs/project/` para capturar continuidad, arquitectura y contexto operativo

El siguiente foco ya no es montar más piezas nuevas de inmediato, sino consolidar y completar la documentación del proyecto para que el stack quede correctamente descrito antes de avanzar hacia tablas vectoriales reales y automatización con `n8n`.