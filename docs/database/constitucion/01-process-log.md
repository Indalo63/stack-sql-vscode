# Process Log – Base de datos legislativa CE

> **Nota histórica (2026-06-23):** Esta bitácora documenta la construcción original del módulo legislativo sobre el schema `legislacion.*`. Ese schema fue posteriormente reemplazado por `normas.*` (multi-ley, `ley_id` FK). Los pasos aquí registrados siguen siendo válidos como referencia del proceso de diseño; ver `docs/project/03-chronological-log.md` Steps 12-19 para la evolución posterior.

## Propósito de este documento

Registra paso a paso la construcción de la base de datos legislativa sobre la Constitución Española, desde la definición del módulo hasta la activación de búsqueda semántica con pgvector.

Cada paso documenta el objetivo, las acciones realizadas, el resultado obtenido y el estado actual. Sirve como guía de replicación y como historial de decisiones técnicas.

## Cómo leer esta bitácora

Los pasos están ordenados por secuencia real de construcción. No saltar pasos: cada uno es prerequisito del siguiente.

---

## Paso 1 – Definición del módulo y encuadre

### Objetivo

Establecer el propósito, alcance y estructura del módulo antes de tocar la base de datos o crear archivos SQL.

### Acciones

- Confirmación de la Constitución Española (1978) como ley fuente
- Identificación del permalink ELI oficial del BOE como fuente de datos
- Definición del objetivo real: base técnica para una app de Q&A jurídico con búsqueda semántica
- Diseño de la estructura de archivos SQL y documentación
- Creación del archivo `docs/database/constitucion/00-overview.md`

### Resultado

El módulo quedó encuadrado con objetivo claro, fuente de datos oficial identificada y estructura de archivos definida antes de escribir una sola línea de SQL.

### Estado

Completado.

---

## Paso 2 – Diseño del esquema relacional

### Objetivo

Definir las tablas necesarias para almacenar la jerarquía legislativa de la CE y crear el script DDL.

### Acciones

- Análisis de la estructura jerárquica de la CE: preámbulo, títulos, capítulos, secciones, artículos y disposiciones
- Diseño del esquema `legislacion` con sus tablas y relaciones
- Decisión sobre tipos de datos (texto, claves foráneas, campos opcionales)
- Creación del script `sql/ddl/002_constitucion_schema.sql`
- Ejecución del DDL contra `stack_db`

### Resultado

Esquema `legislacion` creado con 5 tablas, 7 índices de navegación y 1 índice HNSW para búsqueda semántica. Ejecutado correctamente contra `stack_db`.

### Estado

Completado.

---

## Paso 3 – Extracción del texto oficial de la CE

### Objetivo

Obtener el texto literal completo de los 169 artículos y las disposiciones desde el BOE.

### Acciones

- Descarga del HTML completo del permalink ELI con `curl` (208 KB)
- Análisis de la estructura del HTML: cada artículo tiene `id="a1"` … `id="a169"`, los títulos `id="tpreliminar"`, `id="ti"` … `id="tx"`, capítulos `id="cprimero"` … y disposiciones con IDs propios
- Escritura de parser Python para extraer texto literal, limpiar entidades HTML y construir el árbol jerárquico
- Generación automática de `sql/dml/002_constitucion_seed.sql` con todos los INSERT

### Resultado

185 elementos extraídos del texto oficial BOE: 1 preámbulo + 169 artículos + 4 disposiciones adicionales + 9 disposiciones transitorias + 1 disposición derogatoria + 1 disposición final. Archivo generado en `sql/dml/002_constitucion_seed.sql`.

### Estado

Completado.

---

## Paso 4 – Carga de datos

### Objetivo

Insertar el texto completo de la CE en la base de datos respetando la jerarquía del esquema.

### Acciones

- Ejecución de `sql/dml/002_constitucion_seed.sql` contra `stack_db`
- Inserción en orden: 1 ley → 11 títulos → 11 capítulos → 2 secciones → 185 artículos/disposiciones
- Transacción única con `BEGIN` / `COMMIT`, sin errores

### Resultado

209 operaciones completadas sin errores. Recuento final verificado en base de datos:
- `leyes`: 1 | `titulos`: 11 | `capitulos`: 11 | `secciones`: 2 | `articulos`: 185
- Desglose por tipo: 169 artículos + 9 DT + 4 DA + 1 DD + 1 DF + 1 preámbulo

### Estado

Completado.

---

## Paso 5 – Verificación de integridad y primeras consultas

### Objetivo

Confirmar que los datos cargados son completos, la jerarquía es coherente y las consultas funcionan.

### Acciones

- 7 checks de integridad ejecutados: contenido vacío, secuencia 1-169, coherencia FK, orden global
- Distribución verificada por título: 9+46+10+31+11+9+11+9+22+7+4 = 169 artículos
- Creación del archivo `sql/queries/constitucion_preguntas.sql` con 4 bloques de consultas:
  - Navegación jerárquica (título > capítulo > sección)
  - Consultas de contenido para Q&A
  - Búsqueda por palabra clave (`ILIKE`)
  - Plantillas para generación automática de preguntas

### Resultado

7/7 checks en verde. Consultas verificadas en base de datos: texto literal correcto, búsqueda por palabra clave operativa, artículos cortos identificados para Q&A directas.

### Estado

Completado.

---

## Paso 6 – Activación de búsqueda semántica (pgvector)

### Objetivo

Preparar el esquema para almacenar embeddings y habilitar búsqueda por similitud sobre el articulado.

### Acciones

- Columna `embedding vector(1536)` y índice HNSW (`vector_cosine_ops`) ya presentes desde el DDL
- Prueba del índice HNSW con vector sintético: similitud coseno = 1 confirmada
- Creación de `scripts/generate_embeddings.py`: genera embeddings con `text-embedding-3-small` (OpenAI, 1536 dims), incorpora contexto jerárquico al texto, carga en la DB por lotes de 50
- Añadido bloque 5 en `sql/queries/constitucion_preguntas.sql` con patrones de búsqueda semántica por similitud coseno

### Resultado

Infraestructura pgvector operativa y verificada. 185 artículos listos para recibir embeddings. El script de generación está pendiente de ejecutar con una clave `OPENAI_API_KEY`.

### Estado

Completado. 185/185 embeddings generados y verificados. Búsqueda semántica operativa.

---

## Checkpoint de este módulo

Último paso de este módulo: **Paso 6** (completado con schema `legislacion.*`)

**Estado posterior:** La CE fue migrada a `normas.articulos` con `ley_id = 1` durante el Step 15 del proyecto (expansión multi-ley). Los 185 artículos, los embeddings y la búsqueda semántica siguen operativos bajo el nuevo schema. Ver `docs/project/03-chronological-log.md` Steps 15-19 para la continuación.
