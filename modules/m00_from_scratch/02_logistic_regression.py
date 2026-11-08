"""
Build 2: logistic regression from scratch.

Business question: from a customer's first year (Sep 2018 - Sep 2019),
what is the PROBABILITY they buy again in the following year?

Run from repo root:  python modules/m00_from_scratch/02_logistic_regression.py
"""
from pathlib import Path

import duckdb
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[2]
con = duckdb.connect(str(ROOT / "data" / "meridian.duckdb"), read_only=True)

# ---------- 1. same year-1 features as build 1; target is now YES/NO ----------
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
        select distinct customer_id
        from main_marts.fct_sales
        where sale_date between date '2019-09-22' and date '2020-09-22'
    )
    select y1.*, coalesce(c.age, 32) as age,
           (y2.customer_id is not null)::int as bought_again
    from y1
    left join y2 using (customer_id)
    left join main_marts.dim_customer c using (customer_id)
    using sample 200000 rows (reservoir, 42)
""").fetchnumpy()

feature_names = ["purchase_days", "units", "spend", "online_share", "days_since_last", "age"]
X = np.column_stack([df[f].astype(float) for f in feature_names])
y = df["bought_again"].astype(float)
print(f"customers: {len(y):,} | bought again: {y.mean():.1%}")

rng = np.random.default_rng(42)
idx = rng.permutation(len(y))
cut = int(0.8 * len(y))
tr, te = idx[:cut], idx[cut:]
mu, sd = X[tr].mean(axis=0), X[tr].std(axis=0)
Xs = (X - mu) / sd

# ---------- 2. the model, from scratch ----------
# score       z = X @ w + b              (any number, -inf..+inf)
# probability p = sigmoid(z) = 1 / (1 + e^-z)   (squashed into 0..1)
# loss        = -mean( y*log(p) + (1-y)*log(1-p) )   "log loss": confident + wrong = huge penalty
# gradient    dL/dw = 1/n * X^T (p - y)   -- same shape as build 1, which is no coincidence
def sigmoid(z):
    return 1 / (1 + np.exp(-z))

def log_loss(y_true, p):
    p = np.clip(p, 1e-12, 1 - 1e-12)              # avoid log(0)
    return -np.mean(y_true * np.log(p) + (1 - y_true) * np.log(1 - p))

w = np.zeros(X.shape[1])
b = 0.0
lr = 0.5
for step in range(3001):
    p = sigmoid(Xs[tr] @ w + b)
    err = p - y[tr]
    w -= lr * (Xs[tr].T @ err) / len(tr)
    b -= lr * err.mean()
    if step % 500 == 0:
        print(f"step {step:>4}  train log loss {log_loss(y[tr], p):.4f}")

# ---------- 3. AUC from scratch ----------
# AUC = chance a random returner scores higher than a random non-returner.
# Trick: rank all scores; AUC = (sum of returners' ranks - n1(n1+1)/2) / (n1 * n0)
def auc(y_true, score):
    order = np.argsort(score)
    ranks = np.empty(len(score))
    ranks[order] = np.arange(1, len(score) + 1)
    n1 = y_true.sum()
    n0 = len(y_true) - n1
    return (ranks[y_true == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

# ---------- 4. referee: scikit-learn (no regularisation, to match ours) ----------
sk = LogisticRegression(C=np.inf, max_iter=1000).fit(Xs[tr], y[tr])
print("\nweights (per 1 std of each feature, in log-odds):")
print(f"{'feature':<18}{'mine':>10}{'sklearn':>10}{'odds x':>10}")
for name, a, s in zip(feature_names, w, sk.coef_[0]):
    print(f"{name:<18}{a:>10.4f}{s:>10.4f}{np.exp(a):>10.2f}")
print(f"{'intercept':<18}{b:>10.4f}{sk.intercept_[0]:>10.4f}")

p_te = sigmoid(Xs[te] @ w + b)
print(f"\nTEST AUC       mine {auc(y[te], p_te):.4f} | sklearn {roc_auc_score(y[te], sk.predict_proba(Xs[te])[:, 1]):.4f} | coin flip 0.5000")
print(f"TEST log loss  mine {log_loss(y[te], p_te):.4f} | baseline (everyone gets {y[tr].mean():.3f}) {log_loss(y[te], np.full(len(te), y[tr].mean())):.4f}")

# ---------- 5. the accuracy trap ----------
acc_model = np.mean((p_te >= 0.5) == y[te])
acc_lazy = np.mean(y[te] == 1)
print(f"\nACCURACY  model {acc_model:.1%} | lazy 'everyone returns' {acc_lazy:.1%}   <- why accuracy misleads")

# ---------- 6. is it useful? top 10% riskiest vs average ----------
risk = 1 - p_te
top = risk >= np.quantile(risk, 0.9)
print(f"churn rate: riskiest 10% {1 - y[te][top].mean():.1%} | everyone {1 - y[te].mean():.1%} "
      f"| lift {(1 - y[te][top].mean()) / (1 - y[te].mean()):.1f}x")
print("MATCH" if abs(auc(y[te], p_te) - roc_auc_score(y[te], sk.predict_proba(Xs[te])[:, 1])) < 1e-3 else "MISMATCH")
