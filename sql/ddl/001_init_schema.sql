-- 001_init_schema.sql
-- Esquema mínimo de ejemplo para el stack SQL + VS Code

CREATE SCHEMA IF NOT EXISTS sales;

CREATE TABLE IF NOT EXISTS sales.customers (
    customer_id   SERIAL PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT UNIQUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales.orders (
    order_id      SERIAL PRIMARY KEY,
    customer_id   INT NOT NULL REFERENCES sales.customers(customer_id),
    order_date    DATE NOT NULL DEFAULT CURRENT_DATE,
    amount        NUMERIC(12,2) NOT NULL,
    status        TEXT NOT NULL DEFAULT 'pending'
);
