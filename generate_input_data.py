import os
import polars as pl

SOURCE_DIR = "Data/BACI_Full"
TARGET_DIR = "Processed Data"
YEARS = list(range(2014, 2024))

os.makedirs(TARGET_DIR, exist_ok=True)

def load_country_map():
    path = os.path.join(SOURCE_DIR, "country_codes_V202501.csv")
    df = pl.read_csv(path)
    return dict(zip(df["country_code"], df["country_name"]))


def load_product_list():
    path = os.path.join(SOURCE_DIR, "product_codes_HS92_V202501.csv")
    df = pl.read_csv(
        path,
        schema_overrides={"code": pl.Utf8}
    ).select([
        pl.col("code").alias("product_code"),
        pl.col("description").alias("product_name")
    ])
    df.write_parquet(os.path.join(TARGET_DIR, "products.parquet"))
    print(f"[✓] Saved products.parquet with {df.shape[0]} rows")


def process_trade_data(country_map):
    dfs = []
    for year in YEARS:
        try:
            file = f"BACI_HS92_Y{year}_V202501.csv"
            path = os.path.join(SOURCE_DIR, file)
            print(f"Processing {file}...")
            df = pl.read_csv(path).select([
                pl.lit(year).alias("year"),
                pl.col("k").cast(pl.Utf8).alias("product_code"),
                pl.col("i").alias("exporter_code"),
                pl.col("j").alias("importer_code"),
                pl.col("v").alias("value_1000usd")
            ])
            df = df.with_columns([
                pl.col("exporter_code").replace(country_map, default=None).alias("exporter"),
                pl.col("importer_code").replace(country_map, default=None).alias("importer")
            ]).drop(["exporter_code", "importer_code"])
            dfs.append(df)
            print(f"  [✓] {df.shape[0]} rows added for {year}")
        except Exception as e:
            print(f"  [!] Failed on {file}: {e}")

    if dfs:
        full_df = pl.concat(dfs)
        full_df.write_parquet(os.path.join(TARGET_DIR, "data_2014_2023.parquet"))
        print(f"[✓] Saved data_2014_2023.parquet with {full_df.shape[0]} rows")
    else:
        print("[✗] No data was processed.")

def main():
    try:
        print("Starting country map load...")
        country_map = load_country_map()
        print(f"[✓] Loaded {len(country_map)} country codes")
    except Exception as e:
        print(f"[✗] Failed loading country codes: {e}")
        return

    try:
        print("Loading and saving product codes...")
        load_product_list()
    except Exception as e:
        print(f"[✗] Failed processing product codes: {e}")
        return

    try:
        print("Starting trade data processing...")
        process_trade_data(country_map)
    except Exception as e:
        print(f"[✗] Failed processing trade data: {e}")

if __name__ == "__main__":
    main()
