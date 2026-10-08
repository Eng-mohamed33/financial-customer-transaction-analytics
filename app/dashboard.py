"""Financial Customer & Transaction Analytics - Streamlit dashboard.

Run:  python -m streamlit run app/dashboard.py
Data: data/dashboard/*.csv (built by scripts/build_dashboard_data.py).
All figures come from SYNTHETIC data and use illustrative fixed FX rates.
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data" / "dashboard"
st.set_page_config(page_title="Financial Analytics (Synthetic Data)", page_icon="📊", layout="wide")


@st.cache_data
def load(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name)


if not (DATA / "monthly_cube.csv").exists():
    st.error("Dashboard data not found. Run `python scripts/build_dashboard_data.py` (or the full pipeline) first.")
    st.stop()

meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
cube, cat = load("monthly_cube.csv"), load("category_cube.csv")
seg, rfm = load("segment_summary.csv"), load("customer_rfm_segments.csv")
cur, anomalies = load("currency_summary.csv"), load("top_anomalies.csv")
rules, quality = load("anomaly_rule_summary.csv"), load("quality_report.csv")

st.title("📊 Financial Customer & Transaction Analytics")
st.warning("**Synthetic data - demo only.** Results do not describe a real bank. Values are USD-equivalent using illustrative fixed FX rates (not market data).")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")
currencies = st.sidebar.multiselect("Currency", sorted(cube["currency"].unique()), default=sorted(cube["currency"].unique()))
include_partial = st.sidebar.checkbox(f"Trends: include partial month ({meta['partial_month']})", value=False, disabled=meta["partial_month"] is None)
st.sidebar.caption(f"Period: {meta['first_date']} -> {meta['last_date']}")

fa = cube[cube["currency"].isin(currencies)]      # full period: Overview totals match the report
f = fa                                            # trends: optionally drop the incomplete final month
if not include_partial and meta["partial_month"]:
    f = fa[fa["month"] != meta["partial_month"]]
fc = cat[cat["currency"].isin(currencies)]


def total(kind: str) -> float:
    return float(fa.loc[fa["kind"] == kind, "value_usd"].sum())


deposits, withdrawals, fees, transfers = total("Deposit"), total("Withdrawal"), total("Fee"), total("Transfer")
ext = fa[fa["kind"] != "Transfer"]
n_ext = int(ext["transactions"].sum())

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Trends", "Customers", "Anomalies", "Data & limitations"])

# ---------------- Overview ----------------
with tab1:
    c = st.columns(5)
    c[0].metric("Transactions (excl. transfers)", f"{n_ext:,}")
    c[1].metric("Total value (USD-eq.)", f"{ext['value_usd'].sum():,.0f}")
    c[2].metric("Deposits", f"{deposits:,.0f}")
    c[3].metric("Withdrawals + fees", f"{withdrawals + fees:,.0f}")
    c[4].metric("Net flow", f"{deposits - withdrawals - fees:,.0f}")
    st.caption(f"Full period. Fees: {fees:,.0f} | Internal transfers (both legs, excluded from value): {transfers:,.0f}")
    left, right = st.columns(2)
    by_kind = ext.groupby("kind")["value_usd"].sum().reset_index()
    left.plotly_chart(px.pie(by_kind, names="kind", values="value_usd", hole=.5, title="Value by transaction type"), width="stretch")
    spend = fc[fc["kind"] == "Withdrawal"].groupby("category")["value_usd"].sum().nlargest(10).reset_index()
    right.plotly_chart(px.bar(spend, x="value_usd", y="category", orientation="h", title="Top 10 spending categories (withdrawals)").update_yaxes(autorange="reversed"), width="stretch")
    by_cur = fa[fa["kind"] != "Transfer"].groupby(["currency", "kind"])["value_usd"].sum().reset_index()
    st.plotly_chart(px.bar(by_cur, x="currency", y="value_usd", color="kind", barmode="stack", title="Value by currency and type (USD-eq.)"), width="stretch")
    st.subheader("Native currency vs USD-equivalent")
    st.dataframe(cur.rename(columns={"total_native_amount": "total (native units)", "total_amount_usd": "total (USD-eq.)"}), hide_index=True, width="stretch")
    st.caption("Native totals must never be added across currencies.")

# ---------------- Trends ----------------
with tab2:
    monthly = f.pivot_table(index="month", columns="kind", values="value_usd", aggfunc="sum", fill_value=0).reset_index()
    for k in ["Deposit", "Withdrawal", "Fee"]:
        if k not in monthly:
            monthly[k] = 0.0
    monthly["Net flow"] = monthly["Deposit"] - monthly["Withdrawal"] - monthly["Fee"]
    st.plotly_chart(px.line(monthly, x="month", y=["Deposit", "Withdrawal", "Fee"], markers=True, title="Monthly flows (USD-eq.)"), width="stretch")
    st.plotly_chart(px.bar(monthly, x="month", y="Net flow", title="Monthly net flow", color="Net flow", color_continuous_scale="RdYlGn"), width="stretch")
    counts = f[f["kind"] != "Transfer"].groupby("month")["transactions"].sum().reset_index()
    st.plotly_chart(px.bar(counts, x="month", y="transactions", title="Monthly transaction count (excl. transfers)"), width="stretch")

# ---------------- Customers ----------------
with tab3:
    st.subheader("RFM segments")
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(seg, x="segment", y=["customer_share_pct", "value_share_pct"], barmode="group", title="Customer share vs value share (%)"), width="stretch")
    c2.plotly_chart(px.scatter(rfm, x="frequency", y="monetary", color="segment", hover_data=["customer_id", "recency_days"], title="Customers: frequency vs value"), width="stretch")
    pick = st.multiselect("Segment filter", sorted(rfm["segment"].unique()), default=sorted(rfm["segment"].unique()))
    st.dataframe(rfm[rfm["segment"].isin(pick)].sort_values("monetary", ascending=False), hide_index=True, width="stretch")
    st.caption("RFM thresholds are quintile-based for this demo; recompute on real data.")

# ---------------- Anomalies ----------------
with tab4:
    st.info("These are *statistical screening flags*, not fraud findings. Review in context before any decision.")
    st.dataframe(rules, hide_index=True, width="stretch")
    only = st.radio("Show", ["All flagged", "Amount rule", "Frequency rule"], horizontal=True)
    a = anomalies
    if only == "Amount rule" and "amount_anomaly" in a:
        a = a[a["amount_anomaly"]]
    elif only == "Frequency rule" and "frequency_anomaly" in a:
        a = a[a["frequency_anomaly"]]
    st.caption(f"Top {len(a):,} by anomaly score (of the top 1,000 stored for the dashboard)")
    st.dataframe(a, hide_index=True, width="stretch")

# ---------------- Data & limitations ----------------
with tab5:
    st.subheader("Data quality checks")
    st.dataframe(quality, hide_index=True, width="stretch")
    st.markdown(
        """
**Limitations**
- Fully synthetic data from a public generator - no real-bank conclusions.
- Currencies converted with *illustrative fixed rates* (`data/reference/fx_rates.csv`).
- `transaction_status = Completed` is an assumption (the source has no status field).
- Internal transfers are shown separately; fees are separate from withdrawals.
- Anomaly flags are screening results, not fraud detection.
"""
    )
