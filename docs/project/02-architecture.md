# Architecture

_Última actualización: 2026-06-23_

## Purpose of this document

Este documento describe la arquitectura del proyecto `stack-sql-vscode` en tres niveles:

- arquitectura actual
- arquitectura objetivo a corto plazo
- posibilidades de evolución futura

Su finalidad es servir como referencia de diseño para entender cómo encajan los componentes actuales, qué papel cumple cada uno y cómo puede crecer el proyecto sin perder coherencia.

## Architectural vision

La visión del proyecto es construir un stack progresivo de trabajo con datos y SQL que empiece siendo simple, didáctico y verificable, pero que pueda evolucionar más adelante hacia automatización, búsqueda vectorial y flujos de tipo RAG.

La idea no es construir desde el principio una plataforma compleja, sino partir de un núcleo pequeño y estable:

- SQL bien estructurado
- PostgreSQL en Docker
- documentación viva dentro del repositorio
- uso disciplinado de Claude como apoyo técnico

A partir de esa base, el proyecto puede ampliarse hacia automatismos con `n8n`, almacenamiento de embeddings con `pgvector`, consultas semánticas y orquestación de flujos más avanzados.

## Current architecture

La arquitectura actual puede resumirse así:

- Windows como sistema anfitrión
- WSL2 con Ubuntu como entorno de desarrollo operativo
- VS Code como editor principal
- Git como control de versiones
- Docker como capa de ejecución local de servicios
- PostgreSQL como base de datos principal
- `pgvector` como extensión para soporte vectorial
- Claude Code como copiloto técnico y documental

Es una arquitectura de una sola máquina de trabajo, local, modular y pensada para aprendizaje, práctica y evolución controlada.

## Current components

### 1. Host and development environment

El sistema anfitrión es Windows, pero el trabajo técnico real se realiza desde WSL2 con Ubuntu.

Esto permite:

- usar una shell Linux real
- mantener compatibilidad con herramientas de desarrollo modernas
- trabajar con Docker, Git y VS Code en un entorno cercano a producción

### 2. Editor and project workspace

VS Code actúa como centro de trabajo.

Desde él se gestionan:

- archivos Markdown
- scripts SQL
- conexión al repositorio
- extensiones de base de datos
- flujo de trabajo con Claude Code

### 3. Version control

Git proporciona trazabilidad del trabajo y permite tratar la documentación como parte del propio proyecto.

La documentación no se considera un artefacto separado, sino una parte versionada del stack.

### 4. Database runtime

La base de datos se ejecuta localmente en Docker a través de `docker/docker-compose.yml`.

El servicio actual usa:

- imagen: `pgvector/pgvector:pg16`
- contenedor: `stack-sql-postgres`
- usuario: `postgres`
- base de datos: `stack_db`
- puerto: `5432`

### 5. Relational data layer

La capa de datos relacional actual es un esquema de práctica llamado `sales`.

Este esquema contiene un modelo mínimo y didáctico:

- `sales.customers`
- `sales.orders`

Su finalidad no es representar un sistema productivo, sino ofrecer una base clara para practicar SQL, documentar consultas y trabajar con Claude sobre ejemplos concretos.

### 6. Vector and semantic layer

La arquitectura incluye soporte vectorial completo con `pgvector`, operativo en dos niveles:

- Embeddings de artículo: `text-embedding-3-small` (1536 dims) — ~1.350 vectores en `normas.articulos`
- Embeddings de título: mismo modelo — 50 vectores en `normas.titulos` (para RAG jerárquico)
- Índices HNSW con similitud coseno en ambas tablas
- Estrategia RAG automática: full-text (<60K tokens) o jerárquico (≥60K tokens)

### 7. Documentation layer

La documentación está distribuida en varias capas:

- `docs/database/` para estructura y esquema
- `docs/sql/` para estilo y recetas de trabajo SQL
- `docs/project/` para contexto general del proyecto, arquitectura, decisiones y continuidad

Esta separación hace que cada documento tenga un propósito claro y evita mezclar detalles SQL con visión de proyecto.

## Current data and workflow model

El modelo actual de trabajo está basado en cuatro piezas:

### 1. Example data model

Existe un esquema pequeño de ejemplo (`sales`) para practicar SQL con entidades simples y relaciones fáciles de entender.

### 2. SQL-first workflow

El trabajo parte de SQL y documentación, no de automatización.

El orden actual es:

1. definir estructura
2. documentar esquema
3. escribir y ejecutar consultas
4. mejorar estilo y claridad
5. preparar evolución técnica posterior

### 3. Documentation-first continuity

El proyecto busca que la continuidad no dependa de recordar conversaciones anteriores, sino de archivos reales dentro del repositorio.

Por eso `docs/project/` pasa a ser una memoria operativa del stack.

### 4. Human + Claude collaboration model

El modelo de trabajo combina:

- decisiones humanas
- ejecución local y verificación manual
- apoyo de Claude para explicar, generar, refactorizar y ordenar el trabajo

## Current role of Claude in the architecture

Claude cumple ahora un doble papel en el proyecto:

**Como componente de runtime** (vía Anthropic API):
- recibe artículos constitucionales como contexto y genera respuestas fundamentadas (modo Q&A)
- genera preguntas tipo test a partir del texto de los artículos (modo test)
- modelo en uso: `claude-sonnet-4-6`

**Como copiloto de desarrollo** (vía Claude Code):
- ayuda a generar SQL, explicar consultas y refactorizar código
- propone mejoras de estructura y documenta el proyecto
- actúa como profesor y apoyo de arquitectura

Claude se apoya en archivos de contexto concretos:

- `CLAUDE.md`
- `docs/database/schema-summary.md`
- `docs/sql/style-guide.md`
- `docs/sql/prompt-recipes.md`
- `docs/project/`

## Short-term target architecture

- ~~evaluar la calidad de los pipelines Q&A y generación de tests~~ ✅ (2026-06-18)
- ~~expansión a leyes prioritarias GACE (LPAC, LRJSP, TREBEP, LGP, LCSP)~~ ✅ (2026-06-23)
- ~~sincronización automática con el BOE~~ ✅ (2026-06-23)
- ~~RAG jerárquico + mejoras de calidad Q&A + filtrado generador~~ ✅ (2026-06-23)
- **añadir interfaz web Streamlit multi-ley** (Hito 2 — siguiente)
- exportar banco de tests a CSV / Moodle XML (Hito 3)
- simulacro de examen GACE completo (Hito 6)
- módulo de oposiciones con banco histórico + few-shot (Hito 7)

En esta fase, el foco está en la usabilidad, la extensión del contenido legislativo y la integración con fuentes externas.

## Medium-term evolution path

Una vez validada la base actual, la evolución natural del proyecto puede ser:

1. mantener PostgreSQL como núcleo relacional y vectorial
2. añadir una tabla realista de embeddings
3. probar consultas de similitud con casos pequeños
4. instalar `n8n` en Docker
5. conectar `n8n` a `stack_db`
6. construir automatismos básicos sobre esa base
7. evolucionar hacia workflows RAG más completos

En esta etapa, `n8n` pasaría a desempeñar un papel claro de orquestación:

- ingestión de contenido
- generación de embeddings
- escritura en PostgreSQL
- recuperación de contexto
- encadenamiento con modelos de lenguaje

## Possible future extensions

El proyecto debe permanecer abierto a varias líneas de crecimiento, entre ellas:

- integración de `n8n` self-hosted
- workflows RAG locales o híbridos
- uso de modelos de embeddings locales o remotos
- ampliación del modelo de datos más allá de `sales`
- nuevos dominios de práctica SQL
- automatización documental
- pipelines de ingestión de archivos
- visualización o inspección del flujo SQL y de datos
- posible comparación futura entre `pgvector` y una vector database dedicada, si el proyecto lo requiere

Estas extensiones no deben asumirse como obligatorias, pero sí como caminos plausibles de evolución.

## Architectural principles

La evolución de la arquitectura debe seguir estos principios:

### 1. Start simple

Primero se valida una base pequeña y entendible; después se añaden capas nuevas.

### 2. Documentation is part of the system

La documentación no es un añadido opcional, sino parte del diseño operativo del proyecto.

### 3. Verify before automating

Antes de introducir automatización con `n8n`, deben verificarse manualmente la base de datos, la documentación y las consultas vectoriales.

### 4. Keep components modular

Cada capa debe tener una responsabilidad clara:

- Docker ejecuta servicios
- PostgreSQL almacena datos
- `pgvector` aporta capacidad vectorial
- Claude ayuda al desarrollo
- `n8n` orquesta automatismos cuando llegue el momento

### 5. Prefer evolution over premature complexity

No se introducirán componentes nuevos si el proyecto todavía no ha demostrado necesitar esa complejidad.

## Constraints and boundaries

La arquitectura actual tiene límites claros:

- es un entorno local, no un despliegue productivo
- no existe todavía una capa de automatización operativa con `n8n`
- la interfaz de usuario es CLI; la interfaz web Streamlit está pendiente (Hito 2)
- el contenido legislativo cubre 6 leyes GACE; otras leyes pueden añadirse con `parse_boe.py`

Estos límites son importantes para no confundir capacidad potencial con capacidad ya verificada.

## Open architecture questions

Las principales preguntas abiertas son:

- ~~qué interfaz de usuario se construirá sobre el pipeline~~ → **Streamlit** (decidido, Hito 2)
- ~~un proyecto por ley o una base de datos unificada~~ → **schema por área jurídica en `stack_db`** (decidido, ver abajo)
- si el proyecto se apoyará en embeddings de OpenAI o migrará a modelos locales
- cómo se integrará el módulo de oposiciones con el esquema `legislacion` existente (esquema propio `oposiciones` vs. extensión del actual)
- si el proyecto evolucionará hacia un laboratorio de automatización con `n8n` o se mantendrá como stack Python puro

## Architectural decisions

### Modelo de datos para múltiples leyes

**Decisión:** un único esquema `normas.*` en `stack_db` con todas las leyes identificadas por `ley_id`. No hay schemas separados por ley ni por área temática.

**Estructura actual:**
```
stack_db
├── normas.*     ← todas las leyes GACE (CE, LPAC, LRJSP, TREBEP, LGP, LCSP) ✅
├── oposiciones.*  ← banco de preguntas reales (Hito 7, pendiente)
└── sales.*      ← práctica SQL básica
```

**Motivo:** el diseño multi-ley en `normas.*` (leyes + titulos + articulos con ley_id FK) resulta más limpio que crear un schema por ley. Añadir una nueva ley es `parse_boe.py` + `load_ley.py` + `generate_title_embeddings.py`.

**Para dominios completamente distintos** (formación, clientes independientes): ver `docs/project/10-replication-and-domains.md`.

Mientras estas preguntas no estén cerradas, la arquitectura debe seguir tratándose como una base viva y evolutiva.