-- basic_examples.sql
-- Consultas muy simples sobre el esquema sales.

-- 1. Ver todos los clientes
SELECT *
FROM sales.customers;

-- 2. Ver todos los pedidos
SELECT *
FROM sales.orders;

-- 3. Ver clientes y pedidos (join simple)
SELECT
    c.customer_id,
    c.name,
    o.order_id,
    o.order_date,
    o.amount,
    o.status
FROM sales.customers AS c
JOIN sales.orders AS o
  ON o.customer_id = c.customer_id;
