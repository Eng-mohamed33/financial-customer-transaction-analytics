"""Generate clearly synthetic demo data for pipeline testing.

This is not real financial data and must not be used for business conclusions.
Run from the project root: python scripts/generate_sample_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"


def main() -> None:
    rng = np.random.default_rng(SEED)
    OUT.mkdir(parents=True, exist_ok=True)

    n_customers, n_accounts, n_transactions = 100, 150, 2_000
    customer_ids = np.arange(1, n_customers + 1)
    account_ids = np.arange(1, n_accounts + 1)
    branch_ids = np.arange(1, 6)
    product_ids = np.arange(1, 5)

    customers = pd.DataFrame({
        "customer_id": customer_ids,
        "customer_type": rng.choice(["Individual", "Business"], n_customers, p=[0.8, 0.2]),
        "customer_status": rng.choice(["Active", "Inactive"], n_customers, p=[0.85, 0.15]),
        "join_date": pd.Timestamp("2022-01-01") + pd.to_timedelta(rng.integers(0, 1200, n_customers), unit="D"),
    })

    accounts = pd.DataFrame({
        "account_id": account_ids,
        "customer_id": rng.choice(customer_ids, n_accounts),
        "branch_id": rng.choice(branch_ids, n_accounts),
        "product_id": rng.choice(product_ids, n_accounts),
        "account_type": rng.choice(["Checking", "Savings", "Credit"], n_accounts),
        "balance": np.round(rng.lognormal(mean=8.0, sigma=1.0, size=n_accounts), 2),
    })

    transaction_types = ["Deposit", "Withdrawal", "Transfer In", "Transfer Out"]
    transactions = pd.DataFrame({
        "transaction_id": np.arange(1, n_transactions + 1),
        "account_id": rng.choice(account_ids, n_transactions),
        "transaction_type": rng.choice(transaction_types, n_transactions, p=[0.35, 0.25, 0.2, 0.2]),
        "amount": np.round(rng.lognormal(mean=5.5, sigma=1.0, size=n_transactions), 2),
        "transaction_status": rng.choice(["Completed", "Pending", "Failed", "Reversed"], n_transactions, p=[0.9, 0.04, 0.04, 0.02]),
        "transaction_date": pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, n_transactions), unit="D"),
    })

    branches = pd.DataFrame({
        "branch_id": branch_ids,
        "branch_name": [f"Branch {i}" for i in branch_ids],
        "city": rng.choice(["Cairo", "Giza", "Alexandria"], len(branch_ids)),
    })
    products = pd.DataFrame({
        "product_id": product_ids,
        "product_name": ["Basic", "Premium", "Student", "Business"],
        "product_category": ["Deposit", "Deposit", "Deposit", "Business Banking"],
    })

    for name, frame in {
        "customers": customers,
        "accounts": accounts,
        "transactions": transactions,
        "branches": branches,
        "products": products,
    }.items():
        frame.to_csv(OUT / f"{name}.csv", index=False)

    print(f"Wrote synthetic demo data to {OUT}")


if __name__ == "__main__":
    main()
