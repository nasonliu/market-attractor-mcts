from __future__ import annotations

import numpy as np
import pandas as pd


def run_backtest(
    prices: pd.DataFrame,
    target_weights: pd.DataFrame,
    transaction_cost_bps: float,
    initial_capital: float = 1.0,
) -> dict[str, pd.Series | pd.DataFrame]:
    returns = prices.pct_change(fill_method=None).fillna(0.0)
    weights = target_weights.reindex(prices.index).ffill().fillna(0.0)
    weights = weights.reindex(columns=prices.columns, fill_value=0.0)

    held_weights = weights.shift(1).fillna(0.0)
    gross_returns = (held_weights * returns).sum(axis=1)
    turnover = held_weights.diff().abs().sum(axis=1).fillna(0.0)
    costs = turnover * (transaction_cost_bps / 10_000.0)
    net_returns = gross_returns - costs
    equity = initial_capital * (1.0 + net_returns).cumprod()

    return {
        "returns": net_returns,
        "equity": equity,
        "drawdown": compute_drawdown(equity),
        "turnover": turnover,
        "weights": weights,
    }


def compute_drawdown(equity: pd.Series) -> pd.Series:
    return equity / equity.cummax() - 1.0


def summarize_metrics(
    strategy_name: str,
    returns: pd.Series,
    equity: pd.Series,
    drawdown: pd.Series,
    turnover: pd.Series,
    trading_days: int = 252,
) -> dict[str, float | str]:
    returns = returns.dropna()
    years = max((returns.index[-1] - returns.index[0]).days / 365.25, 1e-9)
    total_return = equity.iloc[-1] / equity.iloc[0] - 1.0
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1.0 / years) - 1.0
    ann_vol = returns.std() * np.sqrt(trading_days)
    sharpe = np.nan if ann_vol == 0 else returns.mean() * trading_days / ann_vol
    max_dd = drawdown.min()
    calmar = np.nan if max_dd == 0 else cagr / abs(max_dd)

    return {
        "strategy": strategy_name,
        "total_return": float(total_return),
        "cagr": float(cagr),
        "annual_vol": float(ann_vol),
        "sharpe": float(sharpe),
        "max_drawdown": float(max_dd),
        "calmar": float(calmar),
        "daily_win_rate": float((returns > 0).mean()),
        "avg_daily_turnover": float(turnover.mean()),
    }
