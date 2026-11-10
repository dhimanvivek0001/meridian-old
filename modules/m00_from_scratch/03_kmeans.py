"""
Build 3: K-means clustering from scratch.

Business question: what natural groups of customers does Meridian have,
judged only by HOW they shop (recency, frequency, spend, channel)?

Run from repo root:  python modules/m00_from_scratch/03_kmeans.py
"""
from pathlib import Path

import duckdb
import numpy as np
import polars as pl
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

ROOT = Path(__file__).resolve().parents[2]
con = duckdb.connect(str(ROOT / "data" / "meridian.duckdb"), read_only=True)
pl.Config.set_tbl_cols(10)
pl.Config.set_tbl_width_chars(200)

# ---------- 1. RFM features per customer, as of the last day of data ----------
df = con.sql("""
    select customer_id,
           datediff('day', max(sale_date), date '2020-09-22')          as recency_days,
           count(distinct sale_date)                                    as frequency,
           sum(price_index)                                             as monetary,
           avg(case when sales_channel = 'online' then 1.0 else 0.0 end) as online_share
    from main_marts.fct_sales
    where hash(customer_id) % 14 = 0     -- same ~1/14 of customers every run (reproducible sample)
    group by 1
""").pl()

# k-means measures straight-line distance, so features must be on comparable scales:
# log squashes the long tails (a few customers buy 100x more), then standardise.
X = np.column_stack([
    np.log1p(df["recency_days"].to_numpy()),
    np.log1p(df["frequency"].to_numpy()),
    np.log1p(df["monetary"].to_numpy() * 100),
    df["online_share"].to_numpy(),
]).astype(float)
X = (X - X.mean(axis=0)) / X.std(axis=0)
print(f"customers: {len(X):,}  features: recency, frequency, monetary, online_share")

# ---------- 2. k-means++ start, from scratch ----------
# Pick the 1st centre at random; each next centre is picked with probability
# proportional to its squared distance from the nearest centre so far -> spread-out starts.
def kmeans_pp_init(X, k, rng):
    centres = [X[rng.integers(len(X))]]
    for _ in range(1, k):
        d2 = np.min(((X[:, None, :] - np.array(centres)[None, :, :]) ** 2).sum(axis=2), axis=1)
        centres.append(X[rng.choice(len(X), p=d2 / d2.sum())])
    return np.array(centres)

# ---------- 3. k-means (Lloyd's algorithm), from scratch ----------
# repeat: (a) assign each point to its nearest centre, (b) move each centre to the mean of its points
# stop when no point changes cluster.
def kmeans(X, init, max_iter=300):
    centres = init.copy()
    labels = np.full(len(X), -1)
    for it in range(max_iter):
        d2 = ((X[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2)   # n x k distances
        new_labels = d2.argmin(axis=1)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for j in range(len(centres)):
            if np.any(labels == j):                                      # keep centre if cluster empties
                centres[j] = X[labels == j].mean(axis=0)
    inertia = ((X - centres[labels]) ** 2).sum()                         # total squared distance to own centre
    return labels, centres, inertia, it + 1

# ---------- 4. how many clusters? elbow + silhouette ----------
rng = np.random.default_rng(42)
sample = rng.choice(len(X), size=min(10000, len(X)), replace=False)      # silhouette is O(n^2): sample
print(f"\n{'k':>3}{'inertia':>14}{'silhouette':>12}")
for k in range(2, 9):
    lab, _, inertia, _ = kmeans(X, kmeans_pp_init(X, k, np.random.default_rng(k)))
    print(f"{k:>3}{inertia:>14,.0f}{silhouette_score(X[sample], lab[sample]):>12.3f}")
print("elbow = where inertia stops dropping fast; silhouette: higher = cleaner separation (max 1)")

# ---------- 5. fit k = 5 and check against scikit-learn from the SAME start ----------
K = 5
init = kmeans_pp_init(X, K, np.random.default_rng(7))
labels, centres, inertia, iters = kmeans(X, init)
sk = KMeans(n_clusters=K, init=init, n_init=1, algorithm="lloyd", max_iter=300, tol=0).fit(X)
agree = np.mean(labels == sk.labels_)
print(f"\nk={K}: converged in {iters} iterations | inertia mine {inertia:,.0f} | sklearn {sk.inertia_:,.0f}")
print(f"label agreement with sklearn: {agree:.2%}  ->", "MATCH" if agree > 0.999 else "MISMATCH")

# ---------- 6. profile the clusters in business language ----------
profile = (
    df.with_columns(pl.Series("cluster", labels))
    .group_by("cluster")
    .agg(
        pl.len().alias("customers"),
        (pl.len() / len(df) * 100).round(1).alias("pct"),
        pl.col("recency_days").median().alias("median_recency_days"),
        pl.col("frequency").median().alias("median_purchase_days"),
        pl.col("monetary").median().round(3).alias("median_spend"),
        (pl.col("online_share").mean() * 100).round(0).alias("online_pct"),
        (pl.col("monetary").sum() / df["monetary"].sum() * 100).round(1).alias("pct_of_revenue"),
    )
    .sort("pct_of_revenue", descending=True)
)
print("\ncluster profiles (sorted by share of revenue):")
print(profile)
