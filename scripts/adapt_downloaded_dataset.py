"""Adapt the downloaded synthetic-bank-dataset to this project's contract.

Derived fields are explicitly marked in the project README/report. The source
dataset already contains customer_id in transactions, so no customer join is
needed for transaction ownership.
"""

from pathlib import Path

import pandas as pd


RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def main() -> None:
    accounts = pd.read_csv(RAW / "accounts.csv")
    transactions = pd.read_csv(RAW / "transactions.csv")

    # The source has bank_name but no branch table. Treat each bank preset/name
    # as a branch-like operational unit and create a stable reference table.
    bank_names = pd.Series(accounts["bank_name"].dropna().unique()).sort_values().reset_index(drop=True)
    branch_map = {name: index + 1 for index, name in enumerate(bank_names)}
    accounts["branch_id"] = accounts["bank_name"].map(branch_map).astype("Int64")
    branches = pd.DataFrame({
        "branch_id": range(1, len(bank_names) + 1),
        "branch_name": bank_names,
        "city": "Derived from source bank_name",
        "source_note": "Derived; source did not provide branch records",
    })

    # The source has account_type but no product table. Use account types as
    # product categories and preserve the original value.
    account_types = pd.Series(accounts["account_type"].dropna().unique()).sort_values().reset_index(drop=True)
    product_map = {name: index + 1 for index, name in enumerate(account_types)}
    accounts["product_id"] = accounts["account_type"].map(product_map).astype("Int64")
    products = pd.DataFrame({
        "product_id": range(1, len(account_types) + 1),
        "product_name": account_types,
        "product_category": "Derived from account_type",
        "source_note": "Derived; source did not provide product records",
    })

    # Normalize the transaction contract while preserving the original signed
    # amount for auditability. Current analysis uses positive gross amounts.
    if "timestamp" in transactions.columns:
        transactions = transactions.rename(columns={"timestamp": "transaction_date"})
    transactions["signed_amount"] = transactions["amount"]
    transactions["amount"] = transactions["amount"].abs()
    transactions["source_transaction_type"] = transactions["transaction_type"]
    type_map = {
        "ach_credit": "Deposit",
        "faster_payment": "Deposit",
        "sepa_credit_transfer": "Deposit",
        "internal_transfer": "Transfer",
        "card_payment": "Withdrawal",
        "card_payment_online": "Withdrawal",
        "card_payment_contactless": "Withdrawal",
        "fee": "Withdrawal",
        "atm_withdrawal": "Withdrawal",
        "ach_debit": "Withdrawal",
        "bacs_direct_debit": "Withdrawal",
        "sepa_direct_debit": "Withdrawal",
    }
    transactions["transaction_type"] = transactions["transaction_type"].map(type_map).fillna(transactions["transaction_type"])
    transactions["transaction_status"] = "Completed"

    accounts.to_csv(RAW / "accounts.csv", index=False)
    transactions.to_csv(RAW / "transactions.csv", index=False)
    branches.to_csv(RAW / "branches.csv", index=False)
    products.to_csv(RAW / "products.csv", index=False)
    print(f"Adapted {len(transactions):,} transactions, {len(branches)} derived branches, {len(products)} derived products")


if __name__ == "__main__":
    main()
