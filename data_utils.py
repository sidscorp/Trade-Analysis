import polars as pl
import numpy as np
import streamlit as st

@st.cache_data
def load_trade_data():
    """Load trade data and product list from parquet files"""
    try:
        trade_data = pl.scan_parquet("Processed Data/data_2014_2023.parquet")
        product_list = pl.read_parquet("Processed Data/products.parquet")
        return trade_data, product_list
    except FileNotFoundError as e:
        st.error(f"Error loading data: {e}. Make sure the data files are in the correct directory.")
        st.stop()

def compute_metrics(df):
    """Compute supply chain metrics from trade data"""
    us_imports = df.filter(pl.col("importer") == "USA")
    total_imports = us_imports["value_1000usd"].sum()
    us_exports = df.filter(pl.col("exporter") == "USA")
    total_exports = us_exports["value_1000usd"].sum()

    if total_imports == 0:
        return {
            "risk_score": 0, 
            "diversity_score": 0, 
            "substitutability": 0, 
            "top_supplier_share": 0,
            "top_3_concentration": 0, 
            "num_suppliers": 0, 
            "global_supplier_count": 0, 
            "us_supplier_count": 0,
            "top_exporters": [], 
            "top_importers": [], 
            "us_market_share": 0, 
            "yoy_growth": 0, 
            "trade_balance": 0
        }

    # Calculate supplier shares and market concentration
    supplier_shares = (us_imports.group_by("exporter")
                      .agg(pl.col("value_1000usd").sum())
                      .with_columns((pl.col("value_1000usd") / total_imports).alias("share"))
                      .sort("share", descending=True))

    shares_array = supplier_shares["share"].to_numpy()

    # Identify top exporters and importers
    top_exporters = (df.group_by("exporter")
                    .agg(pl.col("value_1000usd").sum())
                    .sort("value_1000usd", descending=True)
                    .head(5)["exporter"].to_list())

    top_importers = (df.group_by("importer")
                    .agg(pl.col("value_1000usd").sum())
                    .sort("value_1000usd", descending=True)
                    .head(5)["importer"].to_list())

    # Calculate US market share
    us_market_share = (df.filter(pl.col("importer") == "USA")["value_1000usd"].sum() / 
                      df["value_1000usd"].sum() * 100)

    # Calculate year-over-year growth
    yearly_values = (df.filter(pl.col("importer") == "USA")
                    .group_by("year")
                    .agg(pl.col("value_1000usd").sum())
                    .sort("year"))

    yoy_growth = 0
    if len(yearly_values) >= 2:
        latest_year = yearly_values["value_1000usd"].to_list()[-1]
        previous_year = yearly_values["value_1000usd"].to_list()[-2]
        if previous_year != 0:
            yoy_growth = ((latest_year - previous_year) / previous_year) * 100

    # Calculate risk metrics - this uses the Herfindahl-Hirschman Index (HHI) inverted
    # Higher score means lower risk (more diversified)
    risk_score = max(0, min(100, (1 - np.sum(np.square(shares_array))) * 100))
    
    # Calculate diversity score based on number of suppliers
    diversity_score = min(100, (len(supplier_shares) / 10) * 100)
    
    # Calculate substitutability as the ratio of US suppliers to global suppliers
    us_supplier_count = len(us_imports["exporter"].unique())
    global_supplier_count = len(df["exporter"].unique())
    substitutability = min(100, (us_supplier_count / max(1, global_supplier_count)) * 100)
    
    # Calculate concentration metrics
    top_supplier_share = float(shares_array[0]) * 100 if len(shares_array) > 0 else 0
    top_3_concentration = float(np.sum(shares_array[:3])) * 100 if len(shares_array) >= 3 else 0

    return {
        "risk_score": risk_score,
        "diversity_score": diversity_score,
        "substitutability": substitutability,
        "top_supplier_share": top_supplier_share,
        "top_3_concentration": top_3_concentration,
        "num_suppliers": len(supplier_shares),
        "global_supplier_count": global_supplier_count,
        "us_supplier_count": us_supplier_count,
        "top_exporters": top_exporters,
        "top_importers": top_importers,
        "us_market_share": us_market_share,
        "yoy_growth": yoy_growth,
        "trade_balance": total_exports - total_imports
    }