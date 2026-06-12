# SQL Style Guide – Stack SQL + VS Code + PostgreSQL

Estas reglas se aplican a todo el SQL del proyecto, incluyendo el generado por Claude Code.

## 1. Naming

- Usar `snake_case` en todos los identificadores (tablas, columnas, aliases).
- Tablas en plural cuando representan colecciones (customers, orders).
- Clave primaria: `tabla_id` (ej.: `customer_id`, `order_id`).
- Claves foráneas: `nombre_entidad_id` (ej.: `customer_id` en `sales.orders`).

## 2. Esquemas

- Esquema principal de ejemplo: `sales`.
- Referenciar tablas siempre como `sales.nombre_tabla` en ejemplos y consultas.

## 3. SELECT

- Evitar `SELECT *` en consultas de producción; se permite en ejemplos didácticos.
- Orden recomendado: `SELECT` → `FROM` → `JOIN` → `WHERE` → `GROUP BY` → `HAVING` → `ORDER BY` → `LIMIT`.
- Indentar cada cláusula en una nueva línea.

## 4. JOINs

- Usar `JOIN ... ON` explícito, nunca joins implícitos en `WHERE`.
- Alias cortos pero semánticos: `c` para customers, `o` para orders, etc.
- Escribir la condición de join en una línea clara:

```sql
FROM sales.customers AS c
JOIN sales.orders   AS o
  ON o.customer_id = c.customer_id
```

## 5. CTEs (Common Table Expressions)

- Usar CTEs para estructurar consultas complejas.
- Convención de nombres:

  - `base_...` para datos sin filtrar.
  - `filtered_...` para filtros principales.
  - `final_...` para el resultado final.

```sql
WITH base_orders AS (
    SELECT ...
    FROM sales.orders
),
filtered_orders AS (
    SELECT ...
    FROM base_orders
    WHERE ...
)
SELECT *
FROM filtered_orders;
```

## 6. Comentarios

- Añadir comentario encima de cada bloque importante o CTE:

```sql
-- Pedidos por cliente en el último mes
SELECT ...
```

- No comentar cada línea; solo bloques lógicos.

## 7. PostgreSQL específico

- Usar tipos apropiados (numeric, timestamptz, etc.).
- Usar funciones estándar de PostgreSQL cuando mejore claridad (ej.: `NOW()`, `CURRENT_DATE`).
- Evitar sintaxis específica de otros motores (MySQL, SQL Server) salvo que se indique lo contrario.
