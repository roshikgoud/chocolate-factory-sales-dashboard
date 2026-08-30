"""
01_data_cleaning.py
Chocolate Factory Sales Analysis — Data Cleaning & Preparation

Loads the raw multi-sheet Excel workbook (Shipments, Dimension Data, Calendar),
untangles the messy Dimension Data layout, joins everything into a single
analysis-ready fact table, and engineers the Cost / Profit / Margin fields
needed for downstream EDA.
"""

import pandas as pd
import numpy as np

RAW_PATH = "../data/sample-chocolate-shipments-data-all-Apr-2025.xlsx"
OUT_PATH = "../outputs/cleaned_shipments.csv"


def load_raw(path: str) -> dict:
    xl = pd.ExcelFile(path)
    return {
        "shipments": xl.parse("Shipments"),
        "dimensions": xl.parse("Dimension Data", header=None),
    }


def extract_dimension_tables(dim_raw: pd.DataFrame) -> dict:
    """
    The 'Dimension Data' sheet packs three separate lookup tables side-by-side
    with no clean header row — this pulls each one out by its known column
    offsets and gives it a proper schema.
    """
    products = dim_raw.iloc[3:25, [1, 2, 3, 4]].copy()
    products.columns = ["Product", "Category", "Cost_per_box", "PID"]
    products = products.dropna(subset=["PID"])
    products["PID"] = products["PID"].astype(str)
    products["Cost_per_box"] = products["Cost_per_box"].astype(float)

    geography = dim_raw.iloc[3:9, [7, 8, 9]].copy()
    geography.columns = ["Geo", "Region", "GID"]
    geography["GID"] = geography["GID"].astype(str)

    sales_reps = dim_raw.iloc[3:28, [12, 13, 15]].copy()
    sales_reps.columns = ["Sales_person", "Team", "SPID"]
    sales_reps["SPID"] = sales_reps["SPID"].astype(str)

    return {"products": products, "geography": geography, "sales_reps": sales_reps}


def clean_shipments(ship: pd.DataFrame) -> pd.DataFrame:
    df = ship.copy()

    # Standardise key columns to string for safe joins
    for col in ["PID", "GID", "SPID"]:
        df[col] = df[col].astype(str)

    # Null / duplicate checks
    n_before = len(df)
    df = df.dropna(subset=["ShipmentID", "Amount", "Boxes", "Shipdate"])
    df = df.drop_duplicates(subset=["ShipmentID"])
    n_after = len(df)
    print(f"Dropped {n_before - n_after} null/duplicate shipment rows "
          f"({n_before} -> {n_after})")

    # Basic sanity filters — negative or zero amounts/boxes are data errors, not sales
    bad_rows = df[(df["Amount"] <= 0) | (df["Boxes"] <= 0)]
    if len(bad_rows):
        print(f"Removing {len(bad_rows)} rows with non-positive Amount/Boxes")
        df = df[(df["Amount"] > 0) & (df["Boxes"] > 0)]

    df["Shipdate"] = pd.to_datetime(df["Shipdate"])
    return df


def build_fact_table(ship: pd.DataFrame, dims: dict) -> pd.DataFrame:
    df = ship.merge(dims["products"], on="PID", how="left")
    df = df.merge(dims["geography"], on="GID", how="left")
    df = df.merge(dims["sales_reps"], on="SPID", how="left")

    df["Cost"] = df["Cost_per_box"] * df["Boxes"]
    df["Profit"] = df["Amount"] - df["Cost"]
    df["Margin_pct"] = (df["Profit"] / df["Amount"] * 100).round(2)

    df["Year"] = df["Shipdate"].dt.year
    df["Month"] = df["Shipdate"].dt.to_period("M").astype(str)

    return df


def main():
    raw = load_raw(RAW_PATH)
    dims = extract_dimension_tables(raw["dimensions"])
    ship_clean = clean_shipments(raw["shipments"])
    fact = build_fact_table(ship_clean, dims)

    print("\nFinal shape:", fact.shape)
    print("Nulls after join:\n", fact[["Product", "Geo", "Sales_person"]].isna().sum())

    fact.to_csv(OUT_PATH, index=False)
    print(f"\nSaved cleaned fact table to {OUT_PATH}")


if __name__ == "__main__":
    main()
