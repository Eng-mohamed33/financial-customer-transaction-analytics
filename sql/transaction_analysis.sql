-- Transaction volume and value by month and type (USD-equivalent).
SELECT
    DATE_TRUNC('month', CAST(transaction_date AS TIMESTAMP)) AS transaction_month,
    transaction_type,
    COUNT(*) AS transaction_count,
    SUM(amount_usd) AS total_value,
    AVG(amount_usd) AS average_value
FROM transactions
GROUP BY 1, 2
ORDER BY 1, 2;

-- Native-currency totals (never add these across currencies).
SELECT currency, COUNT(*) AS transaction_count, SUM(amount) AS total_native_amount, SUM(amount_usd) AS total_usd_equivalent
FROM transactions
GROUP BY currency
ORDER BY total_usd_equivalent DESC;
