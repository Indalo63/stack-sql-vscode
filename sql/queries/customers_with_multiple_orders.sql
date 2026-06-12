-- Clientes con más de un pedido
-- Esquema: sales | BD: stack_db

-- Versión 1: solo el conteo total
SELECT COUNT(*) AS clientes_con_mas_de_un_pedido
FROM (
    SELECT customer_id
    FROM sales.orders
    GROUP BY customer_id
    HAVING COUNT(*) > 1
) AS subconsulta;


-- Versión 2: detalle de cada cliente y su número de pedidos
SELECT
    c.customer_id,
    c.name,
    COUNT(o.order_id) AS total_pedidos
FROM sales.customers c
JOIN sales.orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) > 1
ORDER BY total_pedidos DESC;
