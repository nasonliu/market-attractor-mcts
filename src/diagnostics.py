from __future__ import annotations

import pandas as pd


POSITION_LEVELS = [0.0, 0.25, 0.5, 0.75, 1.0]


def strategy_position_diagnostics(
    strategy_weights: dict[str, pd.DataFrame],
    asset: str = "SPY",
    trading_days: int = 252,
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for strategy, weights in strategy_weights.items():
        position = weights[asset].fillna(0.0) if asset in weights else pd.Series(0.0, index=weights.index)
        turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
        row: dict[str, float | str] = {
            "strategy": strategy,
            "avg_position": float(position.mean()),
            "annualized_turnover": float(turnover.mean() * trading_days),
            "min_position": float(position.min()),
            "max_position": float(position.max()),
        }
        for level in POSITION_LEVELS:
            row[f"position_{int(level * 100)}pct_days"] = float((position.round(4) == level).mean())
        rows.append(row)
    return pd.DataFrame(rows)


def mcts_regime_position_stats(
    prices: pd.DataFrame,
    regimes: pd.DataFrame,
    mcts_weights: pd.DataFrame,
    regime_rule_weights: pd.DataFrame,
    asset: str = "SPY",
    method: str = "hmm_regime",
) -> pd.DataFrame:
    labels = regimes[method].reindex(prices.index).ffill()
    next_5d = prices[asset].pct_change(5, fill_method=None).shift(-5)
    next_20d = prices[asset].pct_change(20, fill_method=None).shift(-20)

    frame = pd.DataFrame(
        {
            "regime": labels,
            "mcts_position": mcts_weights[asset].reindex(prices.index).ffill(),
            "regime_rule_position": regime_rule_weights[asset].reindex(prices.index).ffill(),
            "next_5d_return": next_5d,
            "next_20d_return": next_20d,
        },
        index=prices.index,
    ).dropna()

    return (
        frame.groupby("regime")
        .agg(
            mcts_avg_position=("mcts_position", "mean"),
            regime_rule_position=("regime_rule_position", "mean"),
            next_5d_return=("next_5d_return", "mean"),
            next_20d_return=("next_20d_return", "mean"),
        )
        .reset_index()
        .sort_values("regime")
    )


def write_diagnostics_markdown(
    path,
    metrics: pd.DataFrame,
    strategy_diagnostics: pd.DataFrame,
    mcts_regime_stats: pd.DataFrame,
) -> None:
    content = f"""# MCTS Diagnostics

## Why the first MCTS version likely lagged

- It sampled independent one-day returns by regime, so a five-day search path could lose the serial structure that trend and volatility regimes depend on.
- The drawdown penalty was high relative to the daily return scale, which encouraged defensive actions even in historically positive regimes.
- Rollouts were guided only by average single-day regime return and had no strong connection to the Regime Rule signal that performed well.
- The search used the full action grid every day, which increased switching and made the strategy pay more transaction costs.

The root-child selection now explicitly uses average value (`child.value / child.visits`). The previous code already did this, and the implementation keeps that behavior.

## Changes in this version

- MCTS defaults to a path sampler: it samples historical continuous SPY return paths from dates that share the current regime.
- The reward is simplified to return minus transaction cost, with a much smaller configurable risk penalty.
- A positive next-20-day regime expectation now creates an opportunity cost for low exposure.
- Regime Rule SPY exposure is used as a prior, and the action set defaults to positions within +/-25 percentage points of that prior.
- Position diagnostics, MCTS position curves, and regime-level MCTS positioning reports are written under `reports/`.

## Latest metrics

```text
{metrics.to_string(index=False)}
```

## Strategy position diagnostics

```text
{strategy_diagnostics.to_string(index=False)}
```

## MCTS by regime

```text
{mcts_regime_stats.to_string(index=False)}
```
"""
    path.write_text(content, encoding="utf-8")
