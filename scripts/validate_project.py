"""Final project QA checks for the synthetic or replacement dataset."""

from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def check(condition: bool, message: str) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {message}")
    if not condition:
        raise SystemExit(1)


def main() -> None:
    raw = ROOT / "data" / "raw"
    processed = ROOT / "data" / "processed"
    visualizations = ROOT / "visualizations"

    for filename in ["customers.csv", "accounts.csv", "transactions.csv"]:
        check((raw / filename).exists(), f"raw/{filename} exists")

    for filename in ["final_dataset.csv", "quality_report.csv", "customer_kpis.csv", "financial_kpis.csv", "customer_rfm_segments.csv"]:
        check((processed / filename).exists(), f"processed/{filename} exists")

    for notebook in sorted((ROOT / "notebooks").glob("*.ipynb")):
        try:
            json.loads(notebook.read_text(encoding="utf-8"))
            valid = True
        except json.JSONDecodeError:
            valid = False
        check(valid, f"{notebook.name} is valid JSON")

    quality = pd.read_csv(processed / "quality_report.csv")
    check((quality["status"] == "pass").all(), "all recorded quality checks pass")

    final_rows = len(pd.read_csv(processed / "final_dataset.csv", usecols=["transaction_id"]))
    check(final_rows > 0, f"final_dataset.csv contains {final_rows:,} transaction rows")

    # ---- Value-level checks (not just file existence) ----
    tx = pd.read_csv(processed / "cleaned_transactions.csv", usecols=["currency", "amount_usd"])
    check("amount_usd" in tx.columns and tx["amount_usd"].notna().all(), "every transaction has a USD-equivalent amount (no mixed-currency sums)")
    kpi = pd.read_csv(processed / "financial_kpis.csv").iloc[0]
    rfm = pd.read_csv(processed / "customer_rfm_segments.csv")
    seg = pd.read_csv(processed / "segment_summary.csv")
    check(abs(seg["value_share_pct"].sum() - 100) < 0.01, "segment value shares sum to 100%")
    expected_total = kpi["total_transaction_value"] + kpi["internal_transfer_volume"]
    check(abs(rfm["monetary"].sum() - expected_total) < 1.0, "RFM monetary total reconciles with financial KPIs")
    parts = kpi["total_deposits"] + kpi["total_withdrawals"] + kpi["total_fees"]
    check(abs(parts - kpi["total_transaction_value"]) < 1.0, "deposits + withdrawals + fees = total transaction value")
    check(abs(tx["amount_usd"].sum() - expected_total) < 1.0, "transaction-level USD total reconciles with KPIs")
    anomalies = pd.read_csv(processed / "anomaly_rule_summary.csv")
    rate = anomalies.loc[anomalies["rule"] == "any_rule", "share_pct"].iloc[0]
    check(rate <= 3.0, f"anomaly screening rate is {rate:.2f}% (<= 3% screening budget)")
    report = (ROOT / "reports" / "business_insights.md").read_text(encoding="utf-8").lower()
    check("synthetic" in report, "business report is labelled as synthetic data")
    check(not list(visualizations.rglob("distribution_*_id.png")), "no meaningless identifier-distribution charts")

    cats = set(pd.read_csv(processed / "cleaned_transactions.csv", usecols=["category"])["category"].unique())
    french = {"alimentation", "restauration", "voyages", "sante", "abonnements", "revenus", "logement", "energie", "professionnel", "famille"}
    check(not (cats & french), "category names are normalized to one language")
    check((ROOT / "data" / "dashboard" / "monthly_cube.csv").exists() and (ROOT / "app" / "dashboard.py").exists(), "dashboard app and its data files exist")

    chart_count = len(list(visualizations.rglob("*.png")))
    check(chart_count >= 30, f"visualization catalog contains {chart_count} PNG files")
    print("Project QA completed successfully.")


if __name__ == "__main__":
    main()
