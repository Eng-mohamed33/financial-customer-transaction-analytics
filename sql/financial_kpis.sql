-- Core financial KPIs (USD-equivalent; DuckDB / PostgreSQL compatible).
-- Mirrors notebook 06: fees separated from withdrawals, internal transfers excluded from value.
WITH t AS (
    SELECT
        amount_usd,
        CASE WHEN source_transaction_type = 'fee' THEN 'Fee' ELSE transaction_type END AS kind
    FROM transactions
    WHERE transaction_status = 'Completed'
)
SELECT
    SUM(CASE WHEN kind <> 'Transfer' THEN amount_usd END) AS total_transaction_value,
    AVG(CASE WHEN kind <> 'Transfer' THEN amount_usd END) AS average_transaction_value,
    SUM(CASE WHEN kind = 'Deposit'    THEN amount_usd ELSE 0 END) AS total_deposits,
    SUM(CASE WHEN kind = 'Withdrawal' THEN amount_usd ELSE 0 END) AS total_withdrawals,
    SUM(CASE WHEN kind = 'Fee'        THEN amount_usd ELSE 0 END) AS total_fees,
    SUM(CASE WHEN kind = 'Transfer'   THEN amount_usd ELSE 0 END) AS internal_transfer_volume,
    SUM(CASE WHEN kind = 'Deposit' THEN amount_usd
             WHEN kind IN ('Withdrawal', 'Fee') THEN -amount_usd
             ELSE 0 END) AS net_transaction_flow
FROM t;
