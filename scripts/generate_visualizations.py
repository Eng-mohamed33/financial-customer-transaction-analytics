"""Generate the project's chart catalog from processed outputs.

All charts are descriptive. They are intended for portfolio/report use, not
for operational decisions without reviewing the underlying records.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
VIS = ROOT / "visualizations"
sns.set_theme(style="whitegrid")


def save(fig, folder: str, name: str) -> None:
    target = VIS / folder
    target.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(target / f"{name}.png", dpi=150)
    plt.close(fig)


def main() -> None:
    tx = pd.read_csv(PROCESSED / "final_dataset.csv", low_memory=False)
    # Mixed currencies must never be summed natively: use the USD-equivalent column.
    AMT = "amount_usd" if "amount_usd" in tx.columns else "amount"
    tx["transaction_date"] = pd.to_datetime(tx["transaction_date"], errors="coerce")
    tx = tx[tx["transaction_date"].notna()].copy()
    tx["month"] = tx["transaction_date"].dt.to_period("M").astype(str)
    tx["weekday"] = tx["transaction_date"].dt.day_name()
    tx["hour"] = tx["transaction_date"].dt.hour
    last_ts = tx["transaction_date"].max()
    partial_month = str(last_ts.to_period("M")) if last_ts.day < last_ts.days_in_month else None
    txm = tx[tx["month"] != partial_month]  # monthly trends exclude the incomplete final month

    # Transaction charts
    monthly = txm.groupby("month").agg(count=("transaction_id", "size"), value=(AMT, "sum")).reset_index()
    daily = tx.groupby(tx["transaction_date"].dt.date).agg(count=("transaction_id", "size"), value=(AMT, "sum")).reset_index()
    for y, name, title in [("count", "daily_transaction_count", "Daily Transaction Count"), ("value", "daily_transaction_value", "Daily Transaction Value")]:
        fig, ax = plt.subplots(figsize=(11, 4)); ax.plot(daily.iloc[:, 0], daily[y]); ax.set_title(title); ax.tick_params(axis="x", labelrotation=35); save(fig, "transactions", name)
    for y, name, title in [("count", "monthly_transaction_count", "Monthly Transaction Count"), ("value", "monthly_transaction_value", "Monthly Transaction Value")]:
        fig, ax = plt.subplots(figsize=(11, 4)); ax.plot(monthly["month"], monthly[y], marker="o"); ax.set_title(title); ax.tick_params(axis="x", labelrotation=45); save(fig, "transactions", name)

    for col, prefix in [("transaction_type", "transaction_type"), ("payment_channel", "payment_channel"), ("category", "transaction_category"), ("country", "transaction_country")]:
        if col not in tx: continue
        top = tx.groupby(col)[AMT].agg(["size", "sum"]).sort_values("sum", ascending=False).head(12).reset_index()
        fig, axes = plt.subplots(1, 2, figsize=(13, 5)); sns.barplot(data=top, y=col, x="size", ax=axes[0], color="#4c78a8"); sns.barplot(data=top, y=col, x="sum", ax=axes[1], color="#f58518"); axes[0].set_title("Count"); axes[1].set_title("Value"); save(fig, "transactions", f"{prefix}_count_and_value")

    for col, name in [(AMT, "transaction_amount_boxplot"), ("balance_after_transaction", "balance_distribution")]:
        if col not in tx: continue
        fig, ax = plt.subplots(figsize=(9, 4)); sns.boxplot(x=tx[col].dropna(), ax=ax); ax.set_title(name.replace("_", " ").title()); save(fig, "transactions", name)
    if "hour" in tx:
        hourly = tx.groupby("hour").size().reset_index(name="count"); fig, ax = plt.subplots(figsize=(9, 4)); sns.barplot(data=hourly, x="hour", y="count", ax=ax, color="#59a14f"); ax.set_title("Transactions by Hour"); save(fig, "transactions", "transactions_by_hour")
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday = tx.groupby("weekday").size().reindex(weekday_order).reset_index(name="count"); fig, ax = plt.subplots(figsize=(9, 4)); sns.barplot(data=weekday, x="weekday", y="count", ax=ax, color="#b279a2"); ax.set_title("Transactions by Weekday"); ax.tick_params(axis="x", labelrotation=35); save(fig, "transactions", "transactions_by_weekday")

    # Financial charts
    if "transaction_type" in tx:
        flows = txm.groupby(["month", "transaction_type"])[AMT].sum().reset_index(); fig, ax = plt.subplots(figsize=(12, 5)); sns.lineplot(data=flows, x="month", y=AMT, hue="transaction_type", marker="o", ax=ax); ax.tick_params(axis="x", labelrotation=45); ax.set_title("Monthly Value by Transaction Type"); save(fig, "financial", "monthly_value_by_transaction_type")
    for col, name in [("currency", "value_by_currency_usd_equivalent"), ("country", "value_by_country"), ("merchant_category", "value_by_merchant_category")]:
        if col not in tx: continue
        grouped = tx.groupby(col)[AMT].sum().nlargest(12).sort_values().reset_index(); fig, ax = plt.subplots(figsize=(9, 5)); sns.barplot(data=grouped, y=col, x=AMT, ax=ax, color="#e15759"); ax.set_title(name.replace("_", " ").title()); save(fig, "financial", name)

    # Customer and segmentation charts
    if "customer_id" in tx:
        customer = tx.groupby("customer_id").agg(transaction_count=("transaction_id", "size"), total_value=(AMT, "sum")).reset_index()
        for col, name, title in [("transaction_count", "customer_frequency_distribution", "Customer Transaction Frequency"), ("total_value", "customer_value_distribution", "Customer Monetary Value")]:
            fig, ax = plt.subplots(figsize=(9, 4)); sns.histplot(customer[col], kde=True, ax=ax); ax.set_title(title); save(fig, "customer", name)
        top = customer.nlargest(15, "transaction_count").sort_values("transaction_count"); fig, ax = plt.subplots(figsize=(9, 6)); sns.barplot(data=top, y="customer_id", x="transaction_count", ax=ax, color="#76b7b2"); ax.set_title("Top Customers by Frequency"); save(fig, "customer", "top_customers_by_frequency")
        top_share = customer.nlargest(10, "total_value"); fig, ax = plt.subplots(figsize=(7, 5)); ax.pie(top_share["total_value"], labels=top_share["customer_id"].astype(str), autopct="%.1f%%"); ax.set_title("Top 10 Customer Value Share"); save(fig, "customer", "top_10_customer_value_share")

    rfm_path = PROCESSED / "customer_rfm_segments.csv"
    if rfm_path.exists():
        rfm = pd.read_csv(rfm_path)
        if "segment" in rfm:
            for col, name, title in [("recency_days", "recency_distribution", "Recency Distribution"), ("frequency", "frequency_distribution", "Frequency Distribution"), ("monetary", "monetary_distribution", "Monetary Distribution")]:
                if col not in rfm: continue
                fig, ax = plt.subplots(figsize=(9, 4)); sns.histplot(rfm[col], kde=True, ax=ax); ax.set_title(title); save(fig, "segmentation", name)
            if {"frequency", "monetary"}.issubset(rfm.columns):
                fig, ax = plt.subplots(figsize=(8, 5)); sns.scatterplot(data=rfm, x="frequency", y="monetary", hue="segment", ax=ax); ax.set_title("RFM Frequency vs Monetary Value"); save(fig, "segmentation", "rfm_frequency_vs_monetary")
            if {"recency_days", "monetary"}.issubset(rfm.columns):
                fig, ax = plt.subplots(figsize=(8, 5)); sns.scatterplot(data=rfm, x="recency_days", y="monetary", hue="segment", ax=ax); ax.set_title("RFM Recency vs Monetary Value"); save(fig, "segmentation", "rfm_recency_vs_monetary")

    # Additional descriptive views that remain useful even when optional
    # dimensions are absent from a replacement dataset.
    if "currency" in tx:
        fig, ax = plt.subplots(figsize=(9, 4)); sns.boxplot(data=tx, x="currency", y="amount", ax=ax, showfliers=False); ax.set_title("Transaction Amount by Currency"); save(fig, "financial", "transaction_amount_by_currency")
    if "category" in tx:
        category_count = tx["category"].value_counts().head(12).sort_values().reset_index(); category_count.columns = ["category", "count"]; fig, ax = plt.subplots(figsize=(9, 5)); sns.barplot(data=category_count, y="category", x="count", ax=ax, color="#59a14f"); ax.set_title("Top Categories by Transaction Count"); save(fig, "transactions", "top_categories_by_count")
        category_avg = tx.groupby("category")["amount"].mean().nlargest(12).sort_values().reset_index(); fig, ax = plt.subplots(figsize=(9, 5)); sns.barplot(data=category_avg, y="category", x="amount", ax=ax, color="#edc949"); ax.set_title("Top Categories by Average Amount"); save(fig, "financial", "top_categories_by_average_amount")
    monthly_avg = tx.groupby("month")["amount"].mean().reset_index(); fig, ax = plt.subplots(figsize=(11, 4)); ax.plot(monthly_avg["month"], monthly_avg["amount"], marker="o", color="#af7aa1"); ax.set_title("Monthly Average Transaction Amount"); ax.tick_params(axis="x", labelrotation=45); save(fig, "transactions", "monthly_average_transaction_amount")
    weekday_value = tx.groupby("weekday")["amount"].sum().reindex(weekday_order).reset_index(); fig, ax = plt.subplots(figsize=(9, 4)); sns.barplot(data=weekday_value, x="weekday", y="amount", ax=ax, color="#ff9da6"); ax.set_title("Transaction Value by Weekday"); ax.tick_params(axis="x", labelrotation=35); save(fig, "financial", "transaction_value_by_weekday")

    print("Visualization catalog generated successfully.")


if __name__ == "__main__":
    main()
