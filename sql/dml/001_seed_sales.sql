-- Datos de ejemplo para el esquema sales
-- Proyecto: stack-sql-vscode | BD: stack_db

-- ============================================================
-- sales.customers
-- ============================================================

INSERT INTO sales.customers (name, email) VALUES
    ('Ana García',       'ana.garcia@example.com'),
    ('Carlos López',     'carlos.lopez@example.com'),
    ('Marta Sánchez',    'marta.sanchez@example.com'),
    ('Pedro Ruiz',       NULL),
    ('Lucía Fernández',  'lucia.fernandez@example.com');


-- ============================================================
-- sales.orders
-- ============================================================

INSERT INTO sales.orders (customer_id, order_date, amount, status) VALUES
    (1, '2026-01-10',  150.00, 'completed'),
    (1, '2026-02-14',   89.50, 'completed'),
    (2, '2026-02-20',  320.00, 'pending'),
    (3, '2026-03-05',   45.00, 'cancelled'),
    (3, '2026-03-18',  210.75, 'completed'),
    (4, '2026-04-01',  500.00, 'pending'),
    (5, '2026-04-22',   99.99, 'completed'),
    (5, '2026-05-03',  175.00, 'pending'),
    (2, '2026-05-15',   60.00, 'cancelled'),
    (1, '2026-06-01',  430.25, 'pending');
