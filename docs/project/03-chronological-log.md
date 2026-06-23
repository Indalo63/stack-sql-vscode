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

## Step 12 – Base de datos legislativa CE y búsqueda semántica

### Objetivo

Construir el primer módulo legislativo con texto oficial, jerarquía relacional y embeddings vectoriales.

### Acciones

- Diseño del esquema `legislacion.*` (5 tablas: leyes, titulos, capitulos, secciones, articulos)
- Extracción del texto oficial de la CE desde el BOE (permalink ELI, HTML consolidado)
- Parser Python ad-hoc para extraer los 185 elementos jerárquicos
- Carga en base de datos + generación de 185 embeddings con `text-embedding-3-small`
- Activación de índice HNSW para búsqueda semántica por similitud coseno

### Resultado

Módulo `legislacion.*` operativo con 185 artículos, embeddings generados y búsqueda semántica verificada.
Documentado en `docs/database/constitucion/`.

### Estado

Completado.

---

## Step 13 – Pipeline Q&A y generación de tests

### Objetivo

Construir los dos pipelines de IA sobre el corpus legislativo de la CE.

### Acciones

- Diseño de arquitectura modular: `app/config.py`, `db.py`, `retrieval.py`, `qa_pipeline.py`, `test_pipeline.py`
- Pipeline Q&A: embed_query → search_articles (pgvector) → Claude
- Pipeline de tests: fetch_articles → prompt → Claude → JSON estructurado
- CLIs: `scripts/qa.py` y `scripts/gentest.py`
- Evaluación de calidad: 13/13 preguntas Q&A correctas, 8/8 preguntas test correctas

### Resultado

Dos pipelines operativos y evaluados sobre la CE. Interfaz CLI funcional.

### Estado

Completado. Hito 1 cerrado (2026-06-18).

---

## Step 14 – Alineación con el estilo oficial GACE 2025

### Objetivo

Adaptar el generador de tests al formato exacto del examen de oposiciones GACE 2025.

### Acciones

- Análisis de 4 PDFs del examen oficial GACE 2025 (convocatoria, ejercicios, instrucciones)
- Identificación de 5 brechas entre el generador original y el examen real:
  1. enunciado no citaba la norma completa
  2. opciones en mayúsculas A/B/C/D en lugar de a/b/c/d
  3. distractores conceptualmente distintos en lugar de datos precisos (plazo, porcentaje, órgano)
  4. preguntas de concepto general en lugar de datos exactos
  5. símbolos matemáticos en opciones y explicaciones
- Reescritura de `_build_test_prompt()` en `app/test_pipeline.py` con 5 reglas obligatorias
- Codificación de las reglas en `CLAUDE.md` como normas permanentes del proyecto

### Resultado

Generador alineado con el estilo oficial GACE 2025. Reglas codificadas en CLAUDE.md y en memoria del proyecto.

### Estado

Completado. Las 5 reglas son normas obligatorias no negociables.

---

## Step 15 – Schema multi-ley `normas.*` y parser genérico del BOE

### Objetivo

Escalar el sistema de una ley (CE) a múltiples leyes sin rediseñar la BD.

### Acciones

- Decisión de consolidar todo en un único schema `normas.*` en `stack_db` (en lugar de schemas por área jurídica como estaba planificado)
- Creación del schema `normas.*`: leyes, titulos, capitulos, secciones, articulos (equivalente a `legislacion.*` pero multi-ley con `ley_id` FK)
- Migración de la CE al nuevo schema (`ley_id = 1`)
- Desarrollo de `scripts/parse_boe.py`: parser genérico de textos consolidados BOE (HTML ELI → JSON)
  - Soporta todos los tipos normativos: ley ordinaria, ley orgánica, RDL, constitución
  - Reconoce estructura jerárquica: Libro → Título → Capítulo → Sección → Artículo
  - Maneja sufijos de artículo: bis, ter, quáter, sexies, septies…
  - Maneja ordinales hasta trigésimo para disposiciones adicionales
  - Deduplicación automática con sufijos -b, -c cuando hay colisión
- Desarrollo de `scripts/load_ley.py`: carga JSON en `normas.*`, calcula token_count, llama a embeddings
- Carga de la LPAC (Ley 39/2015): 156 artículos, 156 embeddings

### Resultado

Schema `normas.*` operativo con CE + LPAC. Pipeline de ingesta genérico y repetible: `parse_boe.py` → `load_ley.py` → `generate_embeddings.py`.

### Estado

Completado.

---

## Step 16 – Carga de leyes prioritarias GACE

### Objetivo

Cargar las 4 leyes prioritarias del programa GACE 2025: LRJSP, TREBEP, LGP, LCSP.

### Acciones

- LRJSP (Ley 40/2015): 219 artículos — detectados duplicados por sufijos `quáter`/`sexies` no reconocidos → corrección del regex en `_norm_articulo`
- TREBEP (RDL 5/2015): 137 artículos — carga sin incidencias
- LGP (Ley 47/2003): 225 artículos — carga sin incidencias
- LCSP (Ley 9/2017): 428 artículos — detectados duplicados de títulos por estructura Libro→Título → añadido soporte de nivel Libro en el parser con prefijo LI-, LII-…; detectadas subsecciones → añadido soporte de `Subsección N.ª` en `_norm_seccion`
- Generación de embeddings para los 1.009 artículos de las 4 leyes nuevas
- Corrección de `generate_embeddings.py`: truncado a 30.000 chars para evitar error 400 en artículos muy largos

### Resultado

6 leyes cargadas en `normas.*`. Total: 1.350 artículos con embeddings. Parser del BOE robusto para cualquier ley con estructura estándar.

### Estado

Completado. Hito 4 cerrado (2026-06-23).

---

## Step 17 – RAG jerárquico y mejoras de calidad

### Objetivo

Mejorar la precisión del Q&A en leyes grandes y la calidad general del sistema.

### Acciones

**RAG jerárquico:**
- Columna `embedding vector(1536)` añadida a `normas.titulos`
- Script `scripts/generate_title_embeddings.py`: genera embeddings de título (texto del título + resumen de artículos)
- 50 embeddings de título generados
- `search_articles_hierarchical()` en `retrieval.py`: top-3 títulos por embedding → top-8 artículos dentro de esos títulos → fallback a búsqueda plana si resultado escaso
- `run_qa()` enruta automáticamente: full-text si token_count < 60K, jerárquico si ≥ 60K

**Parámetros de calidad:**
- TOP_K: 5 → 8
- SIMILARITY_THRESHOLD: 0.20 (nuevo — descarta artículos poco relevantes)
- Prompt de contenido reforzado: cita obligatoria, aviso explícito cuando la información no está

**Generador de tests:**
- Filtro de artículos <200 chars y derogados en `fetch_articles()`
- Selección ponderada: `RANDOM() * log(length(contenido))` prioriza artículos más ricos

### Resultado

Q&A más preciso en LRJSP, LGP y LCSP. Generador produce preguntas sobre artículos con contenido suficiente para distractores de calidad.

### Estado

Completado (2026-06-23).

---

## Step 18 – Sincronización automática con el BOE

### Objetivo

Mantener la base de datos legislativa sincronizada con el BOE sin intervención manual.

### Acciones

- Añadidas columnas `content_hash VARCHAR(64)` y `fecha_actualizacion TIMESTAMPTZ` a `normas.leyes`
- Script `scripts/sync_boe.py`:
  - Descarga el texto consolidado de cada ley desde su `url_eli`
  - Calcula SHA-256 del HTML y compara con `content_hash` almacenado
  - Si hash idéntico → sin cambios (~2s por ley, sin coste de API)
  - Si hash diferente → re-parsea, diff artículo a artículo, actualiza solo los modificados, limpia embeddings afectados, llama a `generate_embeddings.py`
  - Actualiza `content_hash` y `fecha_actualizacion`
  - Log con timestamp en `logs/sync_boe.log`
- Script `scripts/cron_sync_boe.sh`: wrapper que carga `.env` antes de ejecutar
- Cron instalado: `0 4 * * 0` (domingos, 04:00)
- Inicialización de hashes de las 6 leyes activas

### Resultado

Sincronización automática operativa. Primera ejecución completa sin errores. La segunda ejecución detectó correctamente "sin cambios" en todas las leyes.

### Estado

Completado. Hito 5 cerrado (2026-06-23).

---

## Step 19 – Revisión y actualización de documentación

### Objetivo

Poner al día toda la documentación del proyecto tras la acumulación de cambios en sesiones anteriores.

### Acciones

- `docs/project/01-current-state.md`: reescrito para reflejar estado real (normas.*, 6 leyes, RAG jerárquico, cron)
- `docs/project/02-architecture.md`: actualización de hitos, capa vectorial y decisiones de datos
- `docs/project/06-next-steps.md`: hitos 4 y 5 marcados como completados; hitos 6 y 7 añadidos
- `docs/project/08-qa-app-architecture.md`: reescrito con diagrama de 3 vías, RAG jerárquico, esquema normas.*, módulos actuales
- `docs/database/schema-summary.md`: reescrito con esquema normas.* y las 6 leyes
- `docs/project/03-chronological-log.md`: esta actualización (steps 12-19)
- `docs/project/05-decisions-and-rationale.md`: corrección de decisión obsoleta sobre schema por área jurídica

### Resultado

Documentación del proyecto sincronizada con el estado real (2026-06-23).

### Estado

Completado (2026-06-23).

---

## Current checkpoint

_2026-06-23_

El proyecto dispone de:

- Stack Docker: PostgreSQL 16 + pgvector + pgAdmin
- Schema `normas.*` multi-ley con 6 leyes prioritarias GACE (CE, LPAC, LRJSP, TREBEP, LGP, LCSP)
- 1.350 artículos/disposiciones con embeddings de artículo + 50 embeddings de título
- Pipeline Q&A con enrutamiento de 3 vías y RAG jerárquico automático
- Generador de tests alineado con estilo oficial GACE 2025 (5 reglas obligatorias)
- Sincronización automática con BOE: cron semanal (domingos 04:00), hash diff incremental
- Parser del BOE genérico y robusto (`parse_boe.py` + `load_ley.py`)
- Documentación completa y sincronizada con el estado real

**Siguiente paso:** interfaz web Streamlit multi-ley (Hito 2).