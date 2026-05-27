from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def identify_regimes(features: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, dict[str, object]]:
    seed = config["project"]["seed"]
    n_regimes = config["regime"]["n_regimes"]

    scaler = StandardScaler()
    raw_x = features.to_numpy(dtype=np.float64)
    raw_x = np.nan_to_num(raw_x, nan=0.0, posinf=0.0, neginf=0.0)
    x = scaler.fit_transform(raw_x)
    x = np.clip(x, -8.0, 8.0)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning, module="sklearn")
        warnings.filterwarnings("ignore", category=RuntimeWarning, module="hmmlearn")

        kmeans = KMeans(
            n_clusters=n_regimes,
            n_init=config["regime"]["kmeans_n_init"],
            random_state=seed,
        )
        kmeans_labels = kmeans.fit_predict(x)

        hmm = GaussianHMM(
            n_components=n_regimes,
            covariance_type=config["regime"]["hmm_covariance_type"],
            n_iter=config["regime"]["hmm_n_iter"],
            random_state=seed,
        )
        hmm.fit(x)
        hmm_labels = hmm.predict(x)

    regimes = pd.DataFrame(
        {
            "kmeans_regime": kmeans_labels,
            "hmm_regime": hmm_labels,
        },
        index=features.index,
    )
    models = {"scaler": scaler, "kmeans": kmeans, "hmm": hmm}
    return regimes, models


def compute_regime_summary(
    prices: pd.DataFrame,
    regimes: pd.DataFrame,
    trading_days: int = 252,
) -> pd.DataFrame:
    spy_returns = prices["SPY"].pct_change(fill_method=None)
    rows: list[dict[str, float | int | str]] = []

    forward = {}
    future_vol = {}
    for horizon in (1, 5, 20):
        forward[horizon] = prices["SPY"].pct_change(horizon, fill_method=None).shift(-horizon)
        future_vol[horizon] = _future_realized_vol(spy_returns, horizon, trading_days)

    aligned = regimes.reindex(prices.index)
    for method in ("kmeans_regime", "hmm_regime"):
        for regime_id in sorted(aligned[method].dropna().unique()):
            mask = aligned[method] == regime_id
            row: dict[str, float | int | str] = {
                "method": method.replace("_regime", ""),
                "regime": int(regime_id),
                "observations": int(mask.sum()),
            }
            for horizon in (1, 5, 20):
                fwd = forward[horizon][mask].dropna()
                vol = future_vol[horizon][mask].dropna()
                row[f"avg_forward_ret_{horizon}d"] = float(fwd.mean())
                row[f"median_forward_ret_{horizon}d"] = float(fwd.median())
                row[f"forward_vol_{horizon}d_ann"] = float(vol.mean())
                row[f"win_rate_{horizon}d"] = float((fwd > 0).mean())
                row[f"downside_vol_{horizon}d_ann"] = float(
                    fwd[fwd < 0].std() * np.sqrt(trading_days / horizon)
                )
                row[f"cvar_5pct_{horizon}d"] = float(fwd[fwd <= fwd.quantile(0.05)].mean())
            rows.append(row)

    return pd.DataFrame(rows).sort_values(["method", "regime"]).reset_index(drop=True)


def _future_realized_vol(returns: pd.Series, horizon: int, trading_days: int) -> pd.Series:
    if horizon == 1:
        return returns.shift(-1).abs() * np.sqrt(trading_days)
    return returns.shift(-1).iloc[::-1].rolling(horizon).std().iloc[::-1] * np.sqrt(trading_days)
