import numpy as np
import pandas as pd
from scipy import stats


def _summ(x):
    x = pd.to_numeric(pd.Series(x), errors="coerce").dropna().astype(float)
    n = len(x)
    if n == 0:
        return {k: np.nan for k in ["mean","median","sd","se","ci95_low","ci95_high","min","q1","q3","max"]} | {"n": 0}
    mean = x.mean(); median = x.median(); sd = x.std(ddof=1) if n > 1 else np.nan
    se = sd / np.sqrt(n) if n > 1 else np.nan
    if n > 1:
        lo, hi = stats.t.interval(0.95, n - 1, loc=mean, scale=se)
    else:
        lo = hi = np.nan
    return {
        "n": n, "mean": mean, "median": median, "sd": sd, "se": se,
        "ci95_low": lo, "ci95_high": hi, "min": x.min(), "q1": x.quantile(.25),
        "q3": x.quantile(.75), "max": x.max()
    }


def summary_table(df, value_col, group_col=None):
    if group_col is None:
        return pd.DataFrame([_summ(df[value_col])])
    rows = []
    for group, g in df.groupby(group_col, dropna=False, sort=False):
        row = {group_col: group}
        row.update(_summ(g[value_col]))
        rows.append(row)
    return pd.DataFrame(rows)
