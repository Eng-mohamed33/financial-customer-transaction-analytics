# Dataset source and adaptation notes

## Source

The downloaded source is the public [`synthetic-bank-dataset`](https://github.com/mbazouz/synthetic-bank-dataset) project. It generates fully synthetic retail banking data; it is not real customer or bank data. The source project is distributed under Apache-2.0.

Generation used for this project:

```text
country: mix
customers: 200
seed: 4242
transaction rows: 476,202
```

## Source-provided tables copied into this project

`customers.csv`, `accounts.csv`, `transactions.csv`, `cards.csv`, `loans.csv`, `merchants.csv`, and `subscriptions.csv`.

## Derived compatibility tables and fields

- `branches.csv`: derived from unique `accounts.bank_name` values because the source does not provide a branch master table.
- `products.csv`: derived from unique `accounts.account_type` values because the source does not provide a product master table.
- `accounts.branch_id` and `accounts.product_id`: added for relational analysis.
- `transactions.transaction_date`: renamed from `timestamp`.
- `transactions.signed_amount`: preserves the source signed amount.
- `transactions.amount`: converted to absolute gross value for the current KPI notebooks.
- `transactions.transaction_type`: normalized to Deposit, Withdrawal, or Transfer while preserving the original in `source_transaction_type`.
- `transactions.transaction_status`: set to `Completed` because the source feed does not provide a status field; this is an analytical assumption, not a source fact.

Replace the files in this folder with approved real/anonymized data before publishing business conclusions.

## Currency handling (added in the analysis layer)

The generated data mixes USD, GBP and EUR. The raw files are untouched; `data/reference/fx_rates.csv` holds *illustrative* fixed rates used to create `amount_usd` during cleaning. They are not market data.
