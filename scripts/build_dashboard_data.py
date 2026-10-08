"""Build small aggregated CSVs for the Streamlit dashboard (data/dashboard/).

The dashboard never reads the 476K-row transaction file, so it can run from a
fresh GitHub clone (or Streamlit Cloud) without the raw/processed data.
All values are USD-equivalent (illustrative fixed FX) and the data is SYNTHETIC.
"""

import json
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "data" / "dashboard"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tx = pd.read_csv(
        PROCESSED / "cleaned_transactions.csv",
        usecols=["transaction_date", "transaction_type", "source_transaction_type", "currency", "category", "amount_usd", "transaction_status"],
        parse_dates=["transaction_date"],
    )
    tx = tx[tx["transaction_status"].astype(str).str.lower() == "completed"].copy()
    tx["kind"] = tx["transaction_type"].astype(str)
    tx.loc[tx["source_transaction_type"].astype(str).str.lower() == "fee", "kind"] = "Fee"
    tx["month"] = tx["transaction_date"].dt.to_period("M").astype(str)

    cube = tx.groupby(["month", "kind", "currency"]).agg(transactions=("amount_usd", "size"), value_usd=("amount_usd", "sum")).reset_index()
    cube.to_csv(OUT / "monthly_cube.csv", index=False)

    cat = tx.groupby(["category", "kind", "currency"]).agg(transactions=("amount_usd", "size"), value_usd=("amount_usd", "sum")).reset_index()
    cat.to_csv(OUT / "category_cube.csv", index=False)

    last = tx["transaction_date"].max()
    meta = {
        "first_date": str(tx["transaction_date"].min().date()),
        "last_date": str(last.date()),
        "partial_month": str(last.to_period("M")) if last.day < last.days_in_month else None,
        "transactions": int(len(tx)),
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    for name in ["segment_summary", "customer_rfm_segments", "financial_kpis", "customer_kpis", "currency_summary", "anomaly_rule_summary", "quality_report"]:
        shutil.copy(PROCESSED / f"{name}.csv", OUT / f"{name}.csv")

    an = pd.read_csv(PROCESSED / "potentially_anomalous_transactions.csv")
    cols = [c for c in ["transaction_id", "customer_id", "transaction_date", "currency", "amount", "amount_usd", "category", "merchant_name", "transaction_type", "amount_anomaly", "frequency_anomaly", "anomaly_score", "customer_day_count"] if c in an.columns]
    an[cols].head(1000).to_csv(OUT / "top_anomalies.csv", index=False)
    print(f"Dashboard data written to {OUT} ({len(list(OUT.glob('*')))} files).")


if __name__ == "__main__":
    main()
