-- Importe total de pedidos por cliente, de mayor a menor
SELECT
    c.customer_id,
    c.name,
    SUM(o.amount) AS total_amount
FROM sales.customers AS c
JOIN sales.orders   AS o
  ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_amount DESC;
