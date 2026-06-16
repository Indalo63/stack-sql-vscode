# Base de datos legislativa – Constitución Española (1978)

## Qué es este módulo

Este módulo documenta el proceso completo de construcción de una base de datos legislativa sobre la Constitución Española (CE), desde el diseño del esquema hasta la carga de datos con el texto oficial íntegro.

No es un ejercicio de práctica SQL genérico. Es la base técnica de una aplicación que genera preguntas sobre el contenido de la CE y resuelve dudas mediante búsqueda semántica.

## Objetivo

Automatizar la creación de una aplicación de Q&A jurídico que:

- almacene el texto literal completo de los 169 artículos de la CE
- permita búsqueda semántica por similitud sobre el articulado (pgvector)
- sirva de fuente de verdad para un modelo de lenguaje que genere preguntas y responda dudas

## Fuente de datos

**Texto oficial:** Constitución Española de 1978, publicada en el BOE.

**Permalink ELI (European Legislation Identifier):**
`https://www.boe.es/eli/es/c/1978/12/27/(1)/con`

El texto cargado en la base de datos corresponde al texto consolidado oficial. Cualquier actualización debe trazarse contra esta URL.

## Arquitectura del módulo

```
sql/ddl/002_constitucion_schema.sql   → definición del esquema legislacion y sus tablas
sql/dml/002_constitucion_seed.sql     → carga del texto completo de la CE
sql/queries/constitucion_preguntas.sql → consultas para exploración y generación de Q&A
```

## Esquema de datos

Jerarquía legislativa modelada en PostgreSQL:

```
legislacion.leyes
    └── legislacion.titulos
            └── legislacion.capitulos
                    └── legislacion.secciones
                            └── legislacion.articulos
                                    └── columna embedding (vector) para pgvector
```

## Stack tecnológico

| Componente     | Tecnología                  |
|----------------|-----------------------------|
| Base de datos  | PostgreSQL 16 (Docker)      |
| Extensión      | pgvector (ya activada)      |
| Imagen Docker  | pgvector/pgvector:pg16      |
| Contenedor     | stack-sql-postgres           |
| Base de datos  | stack_db                    |
| Puerto         | 5432                        |

## Documentación del proceso

| Archivo              | Contenido                                          |
|----------------------|----------------------------------------------------|
| `00-overview.md`     | Este archivo. Encuadre del módulo.                 |
| `01-process-log.md`  | Bitácora paso a paso de todo el proceso.           |
| `02-schema.md`       | Documentación detallada de tablas y relaciones.    |
| `03-queries-guide.md`| Guía de consultas para exploración y Q&A.         |

## Cómo replicar este módulo desde cero

1. Levantar el stack Docker: `docker compose -f docker/docker-compose.yml up -d`
2. Ejecutar el DDL: `psql -h localhost -U postgres -d stack_db -f sql/ddl/002_constitucion_schema.sql`
3. Cargar los datos: `psql -h localhost -U postgres -d stack_db -f sql/dml/002_constitucion_seed.sql`
4. Verificar con las consultas de `sql/queries/constitucion_preguntas.sql`

## Estado

En construcción. Ver `01-process-log.md` para el estado actualizado de cada paso.
