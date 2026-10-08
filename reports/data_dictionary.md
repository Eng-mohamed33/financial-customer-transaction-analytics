# Data Dictionary & Data Contract

> هذا الملف هو نقطة مرجعية. راجع أسماء الأعمدة بعد تشغيل notebook 01 وعدّل أي اختلافات من المصدر الفعلي.

## Expected tables

| Table | Grain | Expected key | Purpose |
|---|---|---|---|
| customers | One row per customer | `customer_id` | Customer profile and status |
| accounts | One row per account | `account_id` | Account ownership and balances |
| transactions | One row per transaction | `transaction_id` | Financial activity |
| branches | One row per branch | `branch_id` | Branch reference data |
| products | One row per product | `product_id` | Product reference data |

For the downloaded `synthetic-bank-dataset`, `branches.csv` is derived from
`accounts.bank_name` and `products.csv` is derived from `accounts.account_type`.
They are compatibility tables, not source-provided bank master data.

## Expected relationship checks

- `accounts.customer_id` should match `customers.customer_id`.
- `transactions.account_id` should match `accounts.account_id`.
- `accounts.branch_id` should match `branches.branch_id` when branch information exists.
- `accounts.product_id` should match `products.product_id` when product information exists.
- Primary keys should be non-null and unique.

## Fields to confirm from the actual source

| Field concept | Candidate name(s) | Validation rule |
|---|---|---|
| Transaction amount | `amount`, `transaction_amount` | Numeric and non-negative unless signed flows are explicitly defined |
| Transaction date | `transaction_date`, `date` | Parseable date |
| Transaction type | `transaction_type`, `type` | Standardized categories |
| Transaction status | `transaction_status`, `status` | Document included statuses |
| Account balance | `balance`, `account_balance` | Numeric; define currency and as-of date |

## Derived fields added by notebook 02

| Field | Meaning |
|---|---|
| `usd_per_unit` | Illustrative fixed FX rate from `data/reference/fx_rates.csv` (NOT market data) |
| `amount_usd` | `amount` x `usd_per_unit` - the amount used by every value KPI |
| `signed_amount_usd` | `signed_amount` x `usd_per_unit` |

## Decisions to document

- Currency: the source mixes USD/GBP/EUR; value KPIs use `amount_usd` (illustrative fixed rates). Amounts are gross; `signed_amount` keeps the sign.
- Which statuses count as completed financial activity.
- Treatment of refunds, reversals, transfers, and duplicate transaction IDs.
- Reporting period and timezone.
- Whether balances are snapshots or current values.
