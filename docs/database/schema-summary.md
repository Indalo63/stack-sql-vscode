# Schema Summary – stack_db

_Última actualización: 2026-06-23_

Resumen de los esquemas activos en la base de datos `stack_db`.

---

## Esquema `sales` — Práctica SQL básica

Modelo mínimo de clientes y pedidos para practicar SQL relacional.

| Tabla | Propósito |
|---|---|
| `sales.customers` | Clientes (`customer_id`, `name`, `email`, `created_at`) |
| `sales.orders` | Pedidos (`order_id`, `customer_id`, `order_date`, `amount`, `status`) |

Scripts: `sql/ddl/001_init_schema.sql`, `sql/dml/001_seed_sales.sql`

---

## Esquema `normas` — Base de datos legislativa multi-ley

Esquema unificado para múltiples leyes con búsqueda semántica mediante pgvector.
Fuente: textos consolidados del BOE (URLs ELI).

### normas.leyes

Metadatos de cada ley cargada.

| Columna | Tipo | Descripción |
|---|---|---|
| `ley_id` | serial PK | Identificador interno |
| `codigo` | text UNIQUE | Código corto (CE, LPAC, LRJSP…) |
| `nombre` | text | Nombre completo oficial |
| `nombre_corto` | text | Nombre abreviado (Ley 39/2015…) |
| `tipo` | text | constitucion, ley_ordinaria, real_decreto_legislativo… |
| `fecha_pub` | date | Fecha de publicación en BOE |
| `url_eli` | text | Permalink ELI al texto consolidado |
| `token_count` | int | Estimación de tokens (chars/4) |
| `content_hash` | varchar(64) | SHA-256 del HTML; detecta modificaciones |
| `fecha_actualizacion` | timestamptz | Última sincronización con BOE |
| `activa` | boolean | False para leyes retiradas |

**Leyes activas:**

| ley_id | codigo | Ley | Artículos | RAG |
|--------|--------|-----|-----------|-----|
| 1 | CE | Constitución Española (1978) | 185 | full-text |
| 4 | Ley 39/2015 | LPAC | 156 | full-text |
| 7 | Ley 40/2015 | LRJSP | 219 | jerárquico |
| 8 | RDL 5/2015 | TREBEP | 137 | full-text |
| 9 | Ley 47/2003 | LGP | 225 | jerárquico |
| 12 | Ley 9/2017 | LCSP | 428 | jerárquico |

### normas.titulos

Títulos jerárquicos de cada ley.

- `titulo_id`, `ley_id` (FK), `numero`, `denominacion`, `orden`
- `embedding vector(1536)` — embedding semántico del título (para RAG jerárquico)
- **50 títulos** con embeddings generados

### normas.capitulos

- `capitulo_id`, `titulo_id` (FK), `numero`, `denominacion`, `orden`

### normas.secciones

- `seccion_id`, `capitulo_id` (FK), `titulo_id` (FK), `numero`, `denominacion`, `orden`
- Incluye subsecciones (prefijo `Sub-N.ª`)

### normas.articulos

Unidad mínima de contenido. Incluye artículos ordinarios y disposiciones.

| Columna | Tipo | Descripción |
|---|---|---|
| `articulo_id` | serial PK | |
| `ley_id` | int FK | Referencia a normas.leyes |
| `titulo_id` | int FK nullable | |
| `capitulo_id` | int FK nullable | |
| `seccion_id` | int FK nullable | |
| `numero` | text | "14", "108 bis", "DA-1", "DF-3"… |
| `tipo` | text | articulo, preambulo, disposicion_adicional, transitoria, derogatoria, final |
| `contenido` | text | Texto completo del artículo |
| `orden_global` | int | Posición en la ley |
| `embedding` | vector(1536) | Vector semántico (`text-embedding-3-small`) |

**Totales:** ~1.350 artículos/disposiciones · ~1.350 embeddings

**Jerarquía:** leyes → titulos → capitulos → secciones → articulos

---

## Extensiones activas

| Extensión | Versión | Propósito |
|---|---|---|
| `plpgsql` | 1.0 | Lenguaje procedural PostgreSQL |
| `vector` | 0.8.2 | Tipos vectoriales y búsqueda semántica (pgvector) |

---

## Índices vectoriales

```sql
-- Artículos: similitud coseno con HNSW
CREATE INDEX ON normas.articulos USING hnsw (embedding vector_cosine_ops);

-- Títulos: similitud coseno con HNSW
CREATE INDEX ON normas.titulos USING hnsw (embedding vector_cosine_ops);
```
