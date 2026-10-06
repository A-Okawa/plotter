from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from scipy import stats


def _f(v):
    s = str(v).strip() if v is not None else ""
    return None if s == "" else float(s)


def _axis(ax, x_min, x_max, x_tick, y_min, y_max, y_tick):
    xmin, xmax, xt = _f(x_min), _f(x_max), _f(x_tick)
    ymin, ymax, yt = _f(y_min), _f(y_max), _f(y_tick)
    if xmin is not None or xmax is not None:
        lo, hi = ax.get_xlim(); ax.set_xlim(xmin if xmin is not None else lo, xmax if xmax is not None else hi)
    if ymin is not None or ymax is not None:
        lo, hi = ax.get_ylim(); ax.set_ylim(ymin if ymin is not None else lo, ymax if ymax is not None else hi)
    if xt is not None and xt > 0: ax.xaxis.set_major_locator(MultipleLocator(xt))
    if yt is not None and yt > 0: ax.yaxis.set_major_locator(MultipleLocator(yt))


def _offsets(y, width=0.01):
    y = np.asarray(y, dtype=float)
    if len(y) <= 1: return np.zeros(len(y))
    span = np.nanmax(y) - np.nanmin(y)
    bw = max(span / 45.0, 1e-9)
    bins = np.round((y - np.nanmin(y)) / bw).astype(int)
    out = np.zeros(len(y))
    for b in np.unique(bins):
        idx = np.where(bins == b)[0]
        patt = [0.0]; k = 1
        while len(patt) < len(idx):
            patt += [-k*width, k*width]; k += 1
        out[idx] = patt[:len(idx)]
    return out


def _err(vals, kind):
    x = pd.to_numeric(pd.Series(vals), errors="coerce").dropna().astype(float)
    if len(x) == 0 or kind == "None": return None
    m = x.mean()
    if kind == "SD":
        s = x.std(ddof=1); return s, s
    if kind == "SE":
        s = x.std(ddof=1)/np.sqrt(len(x)); return s, s
    if kind == "95% CI":
        se = x.std(ddof=1)/np.sqrt(len(x)); lo, hi = stats.t.interval(.95, len(x)-1, loc=m, scale=se); return m-lo, hi-m
    if kind == "Min–Max": return m-x.min(), x.max()-m
    return None


def make_plot(df, graph_type, x_col, y_col, group_col, show_raw, show_mean, show_median,
              show_n, errorbar, trendline, bins, continuous_x, x_min, x_max, x_tick,
              y_min, y_max, y_tick, title, x_label, y_label, point_size, alpha):
    cols = [c for c in [x_col, y_col, group_col] if c]
    d = df[cols].copy()
    if y_col:
        d[y_col] = pd.to_numeric(d[y_col], errors="coerce")
        d = d.dropna(subset=[y_col])
    fig, ax = plt.subplots(figsize=(7.6, 5.2))

    if graph_type == "Histogram":
        vals = pd.to_numeric(d[x_col], errors="coerce").dropna()
        ax.hist(vals, bins=bins, alpha=.75)
        ax.set_xlabel(x_label or x_col); ax.set_ylabel(y_label or "Count")

    elif graph_type in ["Box + raw points", "Violin + raw points"]:
        if continuous_x:
            d[x_col] = pd.to_numeric(d[x_col], errors="coerce"); d = d.dropna(subset=[x_col])
            positions = sorted(float(v) for v in pd.unique(d[x_col]))
            groups = [d.loc[d[x_col] == p, y_col].dropna().values for p in positions]
            width = .35 * min(np.diff(positions)) if len(positions) > 1 else .25
            labels = [str(v) for v in positions]
        else:
            labels = list(pd.unique(d[x_col].astype(str)))
            positions = list(range(1, len(labels)+1))
            groups = [d.loc[d[x_col].astype(str) == lab, y_col].dropna().values for lab in labels]
            width = .55

        if graph_type == "Box + raw points":
            ax.boxplot(groups, positions=positions, widths=width, showfliers=False,
                       medianprops={"linewidth":1.8}, whiskerprops={"linewidth":1.2},
                       capprops={"linewidth":1.2}, boxprops={"linewidth":1.2})
        else:
            vp = ax.violinplot(groups, positions=positions, widths=width, showmeans=False, showmedians=False, showextrema=False)
            for body in vp["bodies"]: body.set_alpha(.25)

        for pos, vals in zip(positions, groups):
            vals = np.asarray(vals, dtype=float)
            if show_raw:
                off = _offsets(vals, max(width/28, .001))
                ax.scatter(np.full(len(vals), pos)+off, vals, s=point_size, alpha=alpha, zorder=3)
            if show_mean and len(vals): ax.scatter([pos],[np.mean(vals)], marker="D", s=max(35, point_size*1.5), zorder=4)
            if show_median and len(vals): ax.scatter([pos],[np.median(vals)], marker="_", s=max(120, point_size*6), zorder=4)

        if not continuous_x:
            ax.set_xticks(positions); ax.set_xticklabels(labels)
        ax.set_xlabel(x_label or x_col); ax.set_ylabel(y_label or y_col)

        # Condition annotation when each X has a single group value.
        if group_col:
            ydat = d[y_col].dropna(); span = max(float(ydat.max()-ydat.min()), 1.0)
            for pos, lab in zip(positions, labels):
                sub = d[d[x_col] == float(lab)] if continuous_x else d[d[x_col].astype(str) == lab]
                gv = sub[group_col].dropna().astype(str).unique()
                if len(gv) == 1: ax.text(pos, ydat.max()+.08*span, gv[0], ha="center", va="bottom", fontsize=9)
        if show_n:
            lo, hi = ax.get_ylim(); yp = lo + .03*(hi-lo)
            for pos, vals in zip(positions, groups): ax.text(pos, yp, f"n={len(vals)}", ha="center", va="bottom", fontsize=9)

    elif graph_type == "Scatter":
        d[x_col] = pd.to_numeric(d[x_col], errors="coerce"); d = d.dropna(subset=[x_col,y_col])
        if group_col:
            for g, sub in d.groupby(group_col, sort=False): ax.scatter(sub[x_col], sub[y_col], s=point_size, alpha=alpha, label=str(g))
            ax.legend(frameon=False)
        else: ax.scatter(d[x_col], d[y_col], s=point_size, alpha=alpha)
        if trendline and len(d) >= 2:
            x, y = d[x_col].astype(float).values, d[y_col].astype(float).values
            slope, intercept, r, p, _ = stats.linregress(x,y); xs = np.linspace(x.min(), x.max(), 200)
            ax.plot(xs, intercept+slope*xs, linewidth=1.5)
            ax.text(.03,.97, f"$R^2$ = {r*r:.3f}\np = {p:.3g}", transform=ax.transAxes, ha="left", va="top")
        ax.set_xlabel(x_label or x_col); ax.set_ylabel(y_label or y_col)

    elif graph_type == "Line":
        d[x_col] = pd.to_numeric(d[x_col], errors="coerce"); d = d.dropna(subset=[x_col,y_col])
        if group_col:
            for g, sub in d.groupby(group_col, sort=False):
                sub = sub.sort_values(x_col); ax.plot(sub[x_col], sub[y_col], marker="o", linewidth=1.4, label=str(g))
            ax.legend(frameon=False)
        else:
            sub = d.sort_values(x_col); ax.plot(sub[x_col], sub[y_col], marker="o", linewidth=1.4)
        ax.set_xlabel(x_label or x_col); ax.set_ylabel(y_label or y_col)

    elif graph_type == "Bar":
        xlevels = list(pd.unique(d[x_col].astype(str))); base = np.arange(len(xlevels))
        if group_col:
            glevels = list(pd.unique(d[group_col].astype(str))); tw=.8; w=tw/max(len(glevels),1)
            for j,g in enumerate(glevels):
                means=[]; lows=[]; highs=[]
                for xl in xlevels:
                    sub = d[(d[x_col].astype(str)==xl)&(d[group_col].astype(str)==g)][y_col]
                    means.append(sub.mean() if len(sub) else np.nan); er=_err(sub,errorbar); lows.append(er[0] if er else 0); highs.append(er[1] if er else 0)
                xp = base-tw/2+w/2+j*w; ax.bar(xp,means,width=w,label=g)
                if errorbar != "None": ax.errorbar(xp,means,yerr=np.vstack([lows,highs]),fmt="none",capsize=4)
            ax.legend(frameon=False)
        else:
            groups=[d[d[x_col].astype(str)==xl][y_col] for xl in xlevels]; means=[g.mean() for g in groups]
            ax.bar(base,means)
            if errorbar != "None":
                ers=[_err(g,errorbar) for g in groups]; ax.errorbar(base,means,yerr=np.vstack([[e[0] for e in ers],[e[1] for e in ers]]),fmt="none",capsize=4)
        ax.set_xticks(base); ax.set_xticklabels(xlevels); ax.set_xlabel(x_label or x_col); ax.set_ylabel(y_label or y_col)

    else:
        raise ValueError(f"Unsupported graph type: {graph_type}")

    if title: ax.set_title(title)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    _axis(ax,x_min,x_max,x_tick,y_min,y_max,y_tick)
    fig.tight_layout()
    return fig, d
