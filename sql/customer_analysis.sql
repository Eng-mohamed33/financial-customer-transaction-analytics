-- Customer-level analysis (USD-equivalent values).

-- Top customers by completed transaction value
SELECT
    customer_id,
    COUNT(*) AS transaction_count,
    SUM(amount_usd) AS total_transaction_value,
    AVG(amount_usd) AS average_transaction_value
FROM transactions
WHERE transaction_status = 'Completed'
GROUP BY customer_id
ORDER BY total_transaction_value DESC;

-- Customers with no account activity in the selected period
SELECT c.customer_id
FROM customers c
LEFT JOIN transactions t ON t.customer_id = c.customer_id
GROUP BY c.customer_id
HAVING COUNT(t.transaction_id) = 0;
