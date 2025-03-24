import polars as pl
import os

DATA_PATH = "Processed Data/data_2014_2023.parquet"
PRODUCTS_PATH = "Processed Data/products.parquet"

def run_descriptive_analytics():
    df = pl.read_parquet(DATA_PATH)
    print(f"\n[✓] Loaded dataset with {df.shape[0]:,} rows and {df.shape[1]} columns")

    print("\n[✦] Unique Counts")
    print(f"  Years: {df['year'].n_unique()}")
    print(f"  Exporters: {df['exporter'].n_unique()}")
    print(f"  Importers: {df['importer'].n_unique()}")
    print(f"  Products: {df['product_code'].n_unique()}")

    print("\n[✦] Top 10 Products by Total Trade Value")
    top_products = (
        df.group_by("product_code")
          .agg(pl.col("value_1000usd").sum().alias("total_value"))
          .sort("total_value", descending=True)
          .head(10)
    )

    product_names = pl.read_parquet(PRODUCTS_PATH)
    top_products = top_products.join(product_names, on="product_code", how="left")
    print(top_products.select(["product_code", "product_name", "total_value"]))

    print("\n[✦] Top 10 Exporter-Importer Pairs")
    top_pairs = (
        df.group_by(["exporter", "importer"])
          .agg(pl.col("value_1000usd").sum().alias("total_value"))
          .sort("total_value", descending=True)
          .head(10)
    )
    print(top_pairs)

    print("\n[✦] Total Trade Value by Year")
    year_summary = (
        df.group_by("year")
          .agg(pl.col("value_1000usd").sum().alias("total_value"))
          .sort("year")
    )
    print(year_summary)

if __name__ == "__main__":
    run_descriptive_analytics()
