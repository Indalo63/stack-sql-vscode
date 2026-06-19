# Replication and Domains

## Purpose of this document

Este documento describe cómo el proyecto `stack-sql-vscode` puede replicarse o extenderse para cubrir dominios de conocimiento distintos a la legislación.

El objetivo es que cualquier decisión futura sobre expansión de dominio parta de una base clara, con casos de uso definidos y procedimientos concretos para cada enfoque.

---

## Principio base

La arquitectura del proyecto tiene dos capas bien separadas:

**Capa genérica (reutilizable sin modificación):**
- Stack Docker: PostgreSQL + pgvector + pgAdmin
- Pipelines Q&A y generación de tests
- Scripts de generación de embeddings y búsqueda semántica
- Interfaz Streamlit (Hito 2)
- Código Python en `app/`

**Capa específica del dominio (solo los datos):**
- Contenido de los artículos / fragmentos de texto
- Scripts DDL y seed de cada dominio
- Parámetros del prompt adaptados al contexto

Esto hace que el 90% del proyecto sea reutilizable en cualquier dominio que maneje texto estructurado.

---

## Casos de uso y enfoques

### Caso A — Nuevo dominio dentro del mismo proyecto

**Cuándo usarlo:**
- El nuevo dominio comparte infraestructura y usuarios con el proyecto actual.
- Ejemplos: añadir derecho laboral, fiscal o administrativo junto a la legislación ya cargada.
- Los usuarios del sistema hacen consultas que pueden cruzar dominios.

**Enfoque:**
Añadir un nuevo schema en `stack_db` para el nuevo dominio, reutilizando la misma estructura de tablas.

```
stack_db
├── legislacion    ← Constitución Española (activo)
├── laboral        ← ET, LOPD, convenios colectivos
├── fiscal         ← LGT, IRPF, IVA, IS
├── administrativo ← LCSP, LRJSP, PAC
└── medicina       ← protocolos clínicos, guías GPC
```

**Procedimiento:**
1. Crear DDL nuevo en `sql/ddl/00X_<dominio>_schema.sql` siguiendo la estructura de `002_constitucion_schema.sql`.
2. Preparar seed en `sql/dml/00X_<dominio>_seed.sql` con el corpus de texto.
3. Ejecutar `scripts/generate_embeddings.py` apuntando al nuevo schema.
4. Los pipelines Q&A y gentest funcionan añadiendo un parámetro `--schema` o `--dominio`.

**Ventaja principal:** todo el código y la infraestructura se comparten. Un solo stack sirve múltiples dominios.

**Limitación:** a medida que el corpus crece, la búsqueda semántica debe filtrar por dominio antes de calcular similitud para evitar resultados irrelevantes.

---

### Caso B — Proyecto paralelo independiente (fork)

**Cuándo usarlo:**
- El nuevo dominio es completamente distinto en contexto, usuarios o entorno (cliente diferente, formación separada, despliegue propio).
- Ejemplos: replicar el sistema para un cliente jurídico, para un centro médico, para formación universitaria en historia o ciencias.
- Se quiere independencia total de datos, configuración y despliegue.

**Enfoque:**
Copiar el repositorio como punto de partida y sustituir únicamente el corpus de datos.

**Procedimiento:**
1. Crear un nuevo repositorio a partir del actual:
   ```bash
   git clone ~/dev/stack-sql-vscode ~/dev/stack-<nuevo-dominio>
   cd ~/dev/stack-<nuevo-dominio>
   git remote remove origin
   git remote add origin <nueva-url-repo>
   ```
2. Limpiar los datos específicos de legislación:
   - Borrar `sql/dml/002_constitucion_seed.sql`
   - Vaciar o adaptar `sql/ddl/002_constitucion_schema.sql`
3. Añadir el corpus del nuevo dominio (mismo formato: id, título, texto).
4. Actualizar `.env` con las claves API y nombre de base de datos.
5. Levantar el stack y ejecutar `scripts/generate_embeddings.py`.

**Ventaja principal:** independencia total. Cada instancia puede evolucionar de forma autónoma.

**Limitación:** el mantenimiento de mejoras en el core (pipelines, scripts) debe propagarse manualmente a cada fork.

---

### Caso C — Plantilla reutilizable (template)

**Cuándo usarlo:**
- Se quiere desplegar múltiples instancias del sistema para diferentes alumnos, clientes o dominios de forma repetible y estandarizada.
- Ejemplo: cada alumno en prácticas recibe su propia instancia del sistema con su propio corpus.

**Enfoque:**
Extraer un repositorio `stack-qa-template` que contenga solo la infraestructura y los pipelines, sin datos de dominio. El corpus se inyecta mediante variables de entorno y archivos de configuración.

**Estructura del template:**
```
stack-qa-template/
├── app/               ← pipelines genéricos (sin referencia a legislación)
├── scripts/           ← generate_embeddings, qa, gentest (parametrizados)
├── sql/ddl/           ← schema genérico con nombre de tabla configurable
├── docker/            ← docker-compose.yml sin cambios
├── .env.example       ← DOMINIO, SCHEMA_NAME, TABLE_NAME, etc.
└── CORPUS_README.md   ← instrucciones para añadir el corpus propio
```

**Procedimiento para usar el template:**
1. Clonar el template.
2. Definir variables en `.env`: nombre del dominio, schema, tabla.
3. Añadir el corpus en formato CSV o SQL.
4. Ejecutar setup: `make setup && make embeddings`.
5. Lanzar la interfaz: `make ui`.

**Ventaja principal:** despliegue en minutos para cualquier dominio. Ideal para formación.

**Limitación:** requiere trabajo previo de parametrización del core. Recomendado después de tener al menos dos dominios activos en producción.

---

## Tabla comparativa

| Criterio | Caso A (mismo proyecto) | Caso B (fork) | Caso C (template) |
|---|---|---|---|
| Infraestructura compartida | Sí | No | No (cada instancia la tiene) |
| Consultas cruzadas entre dominios | Sí | No | No |
| Independencia entre dominios | No | Total | Total |
| Esfuerzo de puesta en marcha | Mínimo | Bajo | Medio (setup inicial del template) |
| Ideal para | Expansión interna del proyecto | Nuevos clientes o contextos distintos | Formación con alumnos |
| Mantenimiento del core | Centralizado | Manual por fork | Centralizado en el template |

---

## Decisión recomendada por horizonte

| Horizonte | Recomendación |
|---|---|
| Corto plazo (Hitos 4-6) | Caso A: añadir dominios jurídicos como schemas en `stack_db` |
| Medio plazo (uso formativo) | Caso B: fork por especialidad o grupo de alumnos |
| Largo plazo (escalado) | Caso C: template parametrizado como producto reutilizable |

---

## Review rule

Este documento debe actualizarse cuando se tome una decisión concreta sobre expansión de dominio o cuando se inicie el primer caso de uso no jurídico.
