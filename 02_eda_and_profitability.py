"""
02_eda_and_profitability.py
Chocolate Factory Sales Analysis — EDA & Profitability Deep-Dive

Runs exploratory analysis on the cleaned fact table and answers the business
questions that matter most: what's selling, what's actually profitable, and
where is the business quietly losing money.
"""

import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = "../outputs/cleaned_shipments.csv"
VISUALS_DIR = "../visuals"

pd.set_option("display.float_format", lambda x: f"{x:,.2f}")


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["Shipdate"])
    return df


def summary_kpis(df: pd.DataFrame):
    print("=== HEADLINE KPIs ===")
    print(f"Total Revenue:     ${df['Amount'].sum():,.0f}")
    print(f"Total Profit:      ${df['Profit'].sum():,.0f}")
    print(f"Overall Margin:    {df['Profit'].sum() / df['Amount'].sum() * 100:.1f}%")
    print(f"Total Boxes:       {df['Boxes'].sum():,.0f}")
    print(f"Total Shipments:   {len(df):,}")
    print(f"Date Range:        {df['Shipdate'].min().date()} to {df['Shipdate'].max().date()}")


def order_status_leakage(df: pd.DataFrame):
    print("\n=== ORDER STATUS BREAKDOWN ===")
    status = df.groupby("Order_Status").agg(
        Shipments=("ShipmentID", "count"), Revenue=("Amount", "sum")
    )
    status["Revenue_pct"] = (status["Revenue"] / df["Amount"].sum() * 100).round(1)
    print(status.sort_values("Revenue", ascending=False))

    cancelled_pct = status.loc["Cancelled", "Revenue_pct"] if "Cancelled" in status.index else 0
    print(f"\n-> {cancelled_pct}% of total order value sits in Cancelled orders.")


def product_profitability(df: pd.DataFrame):
    print("\n=== PRODUCT PROFITABILITY (sorted by margin) ===")
    prod = df.groupby("Product").agg(
        Revenue=("Amount", "sum"), Profit=("Profit", "sum")
    )
    prod["Margin_pct"] = (prod["Profit"] / prod["Revenue"] * 100).round(1)
    prod = prod.sort_values("Margin_pct")
    print(prod)

    losers = prod[prod["Margin_pct"] < 0]
    if len(losers):
        print(f"\n-> {len(losers)} product(s) are sold at a NET LOSS:")
        print(losers)
    return prod


def category_and_region(df: pd.DataFrame):
    print("\n=== CATEGORY MARGIN ===")
    cat = df.groupby("Category").agg(Revenue=("Amount", "sum"), Profit=("Profit", "sum"))
    cat["Margin_pct"] = (cat["Profit"] / cat["Revenue"] * 100).round(1)
    print(cat.sort_values("Margin_pct", ascending=False))

    print("\n=== REGION PERFORMANCE ===")
    reg = df.groupby("Region").agg(Revenue=("Amount", "sum"), Profit=("Profit", "sum"))
    reg["Margin_pct"] = (reg["Profit"] / reg["Revenue"] * 100).round(1)
    print(reg.sort_values("Revenue", ascending=False))


def top_performers(df: pd.DataFrame):
    print("\n=== TOP 6 SALES REPS BY REVENUE ===")
    reps = df.groupby("Sales_person")["Amount"].sum().sort_values(ascending=False).head(6)
    print(reps)

    print("\n=== TOP 6 PRODUCTS BY REVENUE ===")
    prods = df.groupby("Product")["Amount"].sum().sort_values(ascending=False).head(6)
    print(prods)


def yoy_trend(df: pd.DataFrame):
    print("\n=== YEAR-OVER-YEAR REVENUE ===")
    print(df.groupby("Year")["Amount"].sum())


def make_visuals(df: pd.DataFrame):
    # Margin by product — highlight losses
    prod = df.groupby("Product").agg(Revenue=("Amount", "sum"), Profit=("Profit", "sum"))
    prod["Margin_pct"] = (prod["Profit"] / prod["Revenue"] * 100)
    prod = prod.sort_values("Margin_pct")

    colors = ["#c0392b" if m < 0 else "#2c7a4b" for m in prod["Margin_pct"]]
    plt.figure(figsize=(10, 8))
    plt.barh(prod.index, prod["Margin_pct"], color=colors)
    plt.axvline(0, color="black", linewidth=0.8)
    plt.xlabel("Profit Margin (%)")
    plt.title("Profit Margin by Product — Red = Loss-Making")
    plt.tight_layout()
    plt.savefig(f"{VISUALS_DIR}/margin_by_product.png", dpi=150)
    plt.close()

    # Monthly revenue trend
    monthly = df.groupby(df["Shipdate"].dt.to_period("M"))["Amount"].sum()
    plt.figure(figsize=(10, 5))
    monthly.plot(kind="line", marker="o")
    plt.ylabel("Revenue ($)")
    plt.title("Monthly Revenue Trend (Jan 2023 - Mar 2025)")
    plt.tight_layout()
    plt.savefig(f"{VISUALS_DIR}/monthly_revenue_trend.png", dpi=150)
    plt.close()

    print(f"\nSaved charts to {VISUALS_DIR}/")


def main():
    df = load_data()
    summary_kpis(df)
    order_status_leakage(df)
    product_profitability(df)
    category_and_region(df)
    top_performers(df)
    yoy_trend(df)
    make_visuals(df)


if __name__ == "__main__":
    main()
