# Schema Summary – Stack SQL + VS Code + PostgreSQL

Resumen de los esquemas activos en la base de datos `stack_db`.

---

## Esquema `sales` — Práctica SQL básica

Modelo mínimo de clientes y pedidos para practicar SQL relacional.

**Tablas:**

### sales.customers

- Finalidad: almacenar clientes.
- Columnas:
  - `customer_id` (serial, PK)
  - `name` (text, NOT NULL)
  - `email` (text, UNIQUE, opcional)
  - `created_at` (timestamptz, NOT NULL, por defecto NOW())

### sales.orders

- Finalidad: almacenar pedidos de clientes.
- Columnas:
  - `order_id` (serial, PK)
  - `customer_id` (int, NOT NULL, FK → sales.customers)
  - `order_date` (date, NOT NULL, por defecto CURRENT_DATE)
  - `amount` (numeric(12,2), NOT NULL)
  - `status` (text, NOT NULL, por defecto 'pending')

**Relaciones:** 1 cliente → N pedidos

**Scripts:** `sql/ddl/001_init_schema.sql`, `sql/dml/001_seed_sales.sql`

---

## Esquema `legislacion` — Base de datos legislativa CE

Base de datos de la Constitución Española (1978) con búsqueda semántica.

**Fuente:** texto oficial BOE — `https://www.boe.es/eli/es/c/1978/12/27/(1)/con`

**Tablas:**

### legislacion.leyes

- Finalidad: metadatos de la ley fuente.
- 1 fila: Constitución Española (CE1978)

### legislacion.titulos

- Finalidad: 11 títulos jerárquicos (Preliminar + I al X).

### legislacion.capitulos

- Finalidad: 11 capítulos (solo en Títulos I, III y VIII).

### legislacion.secciones

- Finalidad: 2 secciones (solo en Título I, Capítulo Segundo).

### legislacion.articulos

- Finalidad: unidad mínima de contenido — preámbulo, artículos y disposiciones.
- 185 filas: 1 preámbulo + 169 artículos + 15 disposiciones
- Columna `embedding vector(1536)`: vectores semánticos generados con `text-embedding-3-small` (OpenAI)
- Índice HNSW con similitud coseno para búsqueda semántica

**Jerarquía:** leyes → titulos → capitulos → secciones → articulos

**Scripts:** `sql/ddl/002_constitucion_schema.sql`, `sql/dml/002_constitucion_seed.sql`

**Documentación completa:** `docs/database/constitucion/`

---

## Extensiones activas

| Extensión | Versión | Propósito |
|---|---|---|
| `plpgsql` | 1.0 | Lenguaje procedural PostgreSQL |
| `vector` | 0.8.2 | Tipos vectoriales y búsqueda semántica (pgvector) |
