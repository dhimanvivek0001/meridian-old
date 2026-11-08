"""Meridian - Step 1: convert raw H&M CSVs to Parquet.
Run from repo root: python scripts/01_csv_to_parquet.py
"""
from pathlib import Path

import polars as pl

RAW = Path("data/raw")
OUT = Path("data/parquet")
OUT.mkdir(parents=True, exist_ok=True)

# IDs are TEXT, never numbers: article_id has a leading zero (0108775015)
SCHEMA_OVERRIDES = {
    "transactions_train": {
        "t_dat": pl.Date,
        "customer_id": pl.Utf8,
        "article_id": pl.Utf8,
        "price": pl.Float64,
        "sales_channel_id": pl.Int8,
    },
    "customers": {"customer_id": pl.Utf8, "postal_code": pl.Utf8},
    "articles": {"article_id": pl.Utf8, "product_code": pl.Utf8},
}


def convert(name: str) -> None:
    src = RAW / f"{name}.csv"
    dst = OUT / f"{name}.parquet"
    if not src.exists():
        raise FileNotFoundError(f"Missing {src}. Unzip the Kaggle download into data/raw/")
    # scan = lazy: streams in chunks instead of loading 3+ GB into RAM
    pl.scan_csv(src, schema_overrides=SCHEMA_OVERRIDES[name]).sink_parquet(dst, compression="zstd")
    rows = pl.scan_parquet(dst).select(pl.len()).collect().item()
    print(f"{name:<20} {rows:>12,} rows  {dst.stat().st_size / 1e6:>8.1f} MB")


if __name__ == "__main__":
    for table in ["articles", "customers", "transactions_train"]:
        convert(table)
    tx = pl.scan_parquet(OUT / "transactions_train.parquet")
    print(tx.select(
        pl.col("t_dat").min().alias("first_day"),
        pl.col("t_dat").max().alias("last_day"),
        pl.col("customer_id").n_unique().alias("buying_customers"),
        pl.col("article_id").n_unique().alias("articles_sold"),
    ).collect())
