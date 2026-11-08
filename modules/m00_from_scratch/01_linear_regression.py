"""
Build 1: linear regression from scratch with gradient descent.

Business question: from a customer's first year (Sep 2018 - Sep 2019),
predict how much they spend in the following year (Sep 2019 - Sep 2020).

Run from repo root:  python modules/m00_from_scratch/01_linear_regression.py
"""
from pathlib import Path

import duckdb
import numpy as np
from sklearn.linear_model import LinearRegression

ROOT = Path(__file__).resolve().parents[2]
con = duckdb.connect(str(ROOT / "data" / "meridian.duckdb"), read_only=True)

# ---------- 1. data: features from YEAR 1, target from YEAR 2 (no leakage) ----------
df = con.sql("""
    with y1 as (
        select customer_id,
               count(distinct sale_date)                      as purchase_days,
               count(*)::bigint                               as units,
               sum(price_index)                               as spend,
               avg(case when sales_channel = 'online' then 1.0 else 0.0 end) as online_share,
               datediff('day', max(sale_date), date '2019-09-21') as days_since_last
        from main_marts.fct_sales
        where sale_date between date '2018-09-20' and date '2019-09-21'
        group by 1
    ),
    y2 as (
        select customer_id, sum(price_index) as spend_next
        from main_marts.fct_sales
        where sale_date between date '2019-09-22' and date '2020-09-22'
        group by 1
    )
    select y1.*, coalesce(c.age, 32) as age, coalesce(y2.spend_next, 0) as spend_next
    from y1
    left join y2 using (customer_id)
    left join main_marts.dim_customer c using (customer_id)
    using sample 200000 rows (reservoir, 42)       -- 200k customers: plenty, and fast
""").fetchnumpy()

feature_names = ["purchase_days", "units", "spend", "online_share", "days_since_last", "age"]
X = np.column_stack([df[f].astype(float) for f in feature_names])
y = np.log1p(df["spend_next"].astype(float))      # log: spend is very skewed
print(f"customers: {len(y):,} | buy again in year 2: {(df['spend_next'] > 0).mean():.1%}")

# ---------- 2. train / test split (random is OK here: one row per customer) ----------
rng = np.random.default_rng(42)
idx = rng.permutation(len(y))
cut = int(0.8 * len(y))
tr, te = idx[:cut], idx[cut:]

# ---------- 3. standardise: mean 0, std 1 (from TRAIN only, else test info leaks in) ----------
mu, sd = X[tr].mean(axis=0), X[tr].std(axis=0)
Xs = (X - mu) / sd

# ---------- 4. the model, from scratch ----------
# prediction = X @ w + b
# loss       = mean((prediction - y)^2)              mean squared error
# gradients  = how the loss changes if we nudge w or b slightly
#   dL/dw = 2/n * X^T (pred - y)
#   dL/db = 2/n * sum(pred - y)
w = np.zeros(X.shape[1])
b = 0.0
lr = 0.1                                            # learning rate: step size
for step in range(2001):
    pred = Xs[tr] @ w + b
    err = pred - y[tr]
    w -= lr * (2 / len(tr)) * (Xs[tr].T @ err)
    b -= lr * (2 / len(tr)) * err.sum()
    if step % 400 == 0:
        print(f"step {step:>4}  train MSE {np.mean(err ** 2):.4f}")

# ---------- 5. check against scikit-learn ----------
sk = LinearRegression().fit(Xs[tr], y[tr])
print("\nweights (per 1 std of each feature):")
print(f"{'feature':<18}{'mine':>10}{'sklearn':>10}")
for name, a, s in zip(feature_names, w, sk.coef_):
    print(f"{name:<18}{a:>10.4f}{s:>10.4f}")
print(f"{'intercept':<18}{b:>10.4f}{sk.intercept_:>10.4f}")

def r2(y_true, y_pred):
    return 1 - np.sum((y_true - y_pred) ** 2) / np.sum((y_true - y_true.mean()) ** 2)

mine_r2 = r2(y[te], Xs[te] @ w + b)
sk_r2 = r2(y[te], sk.predict(Xs[te]))
base_r2 = r2(y[te], np.full(len(te), y[tr].mean()))
print(f"\nTEST R^2  mine {mine_r2:.4f} | sklearn {sk_r2:.4f} | baseline (predict the average) {base_r2:.4f}")
print("MATCH" if abs(mine_r2 - sk_r2) < 1e-3 else "MISMATCH: check learning rate / steps")
