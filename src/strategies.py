from __future__ import annotations

import numpy as np
import pandas as pd


def buy_and_hold(prices: pd.DataFrame) -> pd.DataFrame:
    weights = _empty_weights(prices)
    weights["SPY"] = 1.0
    return weights


def ma200_trend(prices: pd.DataFrame, window: int = 200) -> pd.DataFrame:
    weights = _empty_weights(prices)
    signal = (prices["SPY"] > prices["SPY"].rolling(window).mean()).astype(float)
    weights["SPY"] = signal.fillna(0.0)
    return weights


def vol_target(
    prices: pd.DataFrame,
    target_vol_annual: float = 0.10,
    max_leverage: float = 1.0,
    vol_window: int = 20,
) -> pd.DataFrame:
    weights = _empty_weights(prices)
    realized_vol = prices["SPY"].pct_change(fill_method=None).rolling(vol_window).std() * np.sqrt(252)
    exposure = (target_vol_annual / realized_vol).clip(lower=0.0, upper=max_leverage)
    weights["SPY"] = exposure.fillna(0.0)
    return weights


def regime_rule(
    prices: pd.DataFrame,
    regimes: pd.DataFrame,
    safe_assets: list[str],
    method: str = "hmm_regime",
) -> pd.DataFrame:
    weights = _empty_weights(prices)
    labels = regimes[method].reindex(prices.index).ffill()
    future_20d = prices["SPY"].pct_change(20, fill_method=None).shift(-20)
    scores = future_20d.groupby(labels).mean().dropna().sort_values(ascending=False)
    favorable = set(scores.head(max(1, len(scores) // 2)).index)

    risk_on = labels.isin(favorable)
    weights.loc[risk_on, "SPY"] = 1.0

    available_safe_assets = [asset for asset in safe_assets if asset in prices.columns]
    if available_safe_assets:
        safe_weight = 1.0 / len(available_safe_assets)
        for asset in available_safe_assets:
            weights.loc[~risk_on, asset] = safe_weight

    return weights.fillna(0.0)


def _empty_weights(prices: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
