from __future__ import annotations

import numpy as np
import pandas as pd


def build_features(prices: pd.DataFrame, config: dict) -> pd.DataFrame:
    tickers = [ticker for ticker in config["data"]["tickers"] if ticker in prices.columns]
    etfs = [ticker for ticker in tickers if ticker != "^VIX"]
    returns = prices[etfs].pct_change(fill_method=None)

    feature_parts: list[pd.DataFrame] = []

    feature_parts.append(
        returns.add_prefix("ret_1d_")
    )
    feature_parts.append(
        prices[etfs].pct_change(5, fill_method=None).add_prefix("ret_5d_")
    )
    feature_parts.append(
        prices[etfs].pct_change(20, fill_method=None).add_prefix("ret_20d_")
    )

    for window in config["features"]["volatility_windows"]:
        vol = returns.rolling(window).std() * np.sqrt(252)
        feature_parts.append(vol.add_prefix(f"vol_{window}d_"))

    for window in config["features"]["ma_windows"]:
        ma_dev = prices[etfs] / prices[etfs].rolling(window).mean() - 1.0
        feature_parts.append(ma_dev.add_prefix(f"ma_dev_{window}d_"))

    for window in config["features"]["relative_strength_windows"]:
        rs = pd.DataFrame(index=prices.index)
        spy_ret = prices["SPY"].pct_change(window, fill_method=None)
        for ticker in ("QQQ", "IWM", "TLT", "GLD"):
            if ticker in prices:
                rs[f"rs_{window}d_{ticker}_vs_SPY"] = prices[ticker].pct_change(
                    window, fill_method=None
                ) - spy_ret
        feature_parts.append(rs)

    if "^VIX" in prices:
        vix = prices["^VIX"]
        vix_features = pd.DataFrame(index=prices.index)
        vix_features["vix_level"] = vix
        vix_features["vix_change_1d"] = vix.pct_change(fill_method=None)
        vix_features["vix_change_5d"] = vix.pct_change(5, fill_method=None)
        z_window = config["features"]["vix_z_window"]
        vix_features["vix_zscore"] = (vix - vix.rolling(z_window).mean()) / vix.rolling(z_window).std()
        feature_parts.append(vix_features)

    features = pd.concat(feature_parts, axis=1)
    features = features.replace([np.inf, -np.inf], np.nan).dropna()
    return features
