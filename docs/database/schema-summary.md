# Schema Summary – Stack SQL + VS Code + PostgreSQL

Esquema de ejemplo mínimo para practicar SQL con PostgreSQL en este proyecto.

## Dominios

- Ventas (sales)
  - Clientes
  - Pedidos

## Esquemas

- `public`
- `sales` → esquema principal para este ejemplo.

## Tablas clave

### sales.customers

- Finalidad: almacenar clientes.
- Columnas:
  - customer_id (serial, PK)
  - name (text, NOT NULL)
  - email (text, UNIQUE, opcional)
  - created_at (timestamptz, NOT NULL, por defecto NOW())

### sales.orders

- Finalidad: almacenar pedidos de clientes.
- Columnas:
  - order_id (serial, PK)
  - customer_id (int, NOT NULL, FK → sales.customers.customer_id)
  - order_date (date, NOT NULL, por defecto CURRENT_DATE)
  - amount (numeric(12,2), NOT NULL)
  - status (text, NOT NULL, por defecto 'pending')

## Relaciones principales

- 1 cliente → N pedidos
  - sales.customers.customer_id
  - sales.orders.customer_id

## Notas

- Este esquema es solo de práctica (no producción).
- Se creó desde el script: sql/ddl/001_init_schema.sql.
