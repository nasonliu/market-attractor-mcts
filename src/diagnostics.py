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


def root_edge_diagnostics(
    root_values: pd.DataFrame,
    action_levels: list[float | int],
    chosen_col: str,
    previous_col: str,
    value_prefix: str,
) -> pd.DataFrame:
    rows = []
    for _, row in root_values.iterrows():
        action_values = {}
        for action in action_levels:
            suffix = int(action * 100) if isinstance(action, float) else int(action)
            value = row.get(f"{value_prefix}{suffix}")
            if pd.notna(value):
                action_values[action] = float(value)
        if not action_values:
            continue

        best_action = max(action_values, key=action_values.get)
        chosen_action = row[chosen_col]
        previous_action = row[previous_col]
        chosen_value = action_values.get(chosen_action)
        previous_value = action_values.get(previous_action)
        best_value = action_values[best_action]
        rows.append(
            {
                "date": row.get("date"),
                "regime": row.get("regime"),
                "previous_action": previous_action,
                "chosen_action": chosen_action,
                "best_action": best_action,
                "chosen_value": chosen_value,
                "previous_value": previous_value,
                "best_value": best_value,
                "chosen_minus_previous": None
                if chosen_value is None or previous_value is None
                else chosen_value - previous_value,
                "best_minus_previous": None
                if previous_value is None
                else best_value - previous_value,
                "switched": chosen_action != previous_action,
                "chose_best": chosen_action == best_action,
            }
        )
    return pd.DataFrame(rows)


def write_diagnostics_markdown(
    path,
    metrics: pd.DataFrame,
    strategy_diagnostics: pd.DataFrame,
    mcts_regime_stats: pd.DataFrame,
    mcts_config: dict,
    root_values: pd.DataFrame,
    multi_asset_templates: pd.DataFrame | None = None,
    multi_asset_root_values: pd.DataFrame | None = None,
    spy_edge_diagnostics: pd.DataFrame | None = None,
    multi_asset_edge_diagnostics: pd.DataFrame | None = None,
) -> None:
    root_rows = []
    for level in POSITION_LEVELS:
        suffix = int(level * 100)
        root_rows.append(
            {
                "action": level,
                "avg_root_value": root_values.get(f"value_{suffix}", pd.Series(dtype=float)).mean(),
                "avg_visits": root_values.get(f"visits_{suffix}", pd.Series(dtype=float)).mean(),
            }
        )
    root_summary = pd.DataFrame(root_rows)
    chosen_counts = root_values["chosen_position"].value_counts(normalize=True).sort_index().to_frame("chosen_share")
    config_frame = pd.DataFrame(
        [{"parameter": key, "value": value} for key, value in mcts_config.items()]
    )
    best_root_action = root_summary.sort_values("avg_root_value", ascending=False)["action"].iloc[0]
    low_action_share = float(root_values["chosen_position"].isin([0.0, 0.25]).mean())
    full_grid_state = (
        "full action grid"
        if bool(mcts_config.get("use_full_action_grid", False))
        else f"prior-restricted grid with prior_band={mcts_config.get('prior_band')}"
    )
    multi_asset_summary = "No multi-asset template diagnostics were supplied."
    multi_asset_root_summary = "No multi-asset root diagnostics were supplied."
    if multi_asset_templates is not None and not multi_asset_templates.empty:
        template_counts = (
            multi_asset_templates["template_name"]
            .value_counts(normalize=True)
            .rename("template_share")
            .to_frame()
        )
        transition_rate = float(multi_asset_templates["template_id"].diff().fillna(0).ne(0).mean())
        multi_asset_summary = (
            f"Daily template transition rate: {transition_rate:.2%}\n\n"
            f"{template_counts.to_string()}"
        )
    if multi_asset_root_values is not None and not multi_asset_root_values.empty:
        rows = []
        template_value_cols = [col for col in multi_asset_root_values.columns if col.startswith("value_template_")]
        for col in template_value_cols:
            suffix = col.replace("value_template_", "")
            rows.append(
                {
                    "template": int(suffix),
                    "avg_root_value": multi_asset_root_values[col].mean(),
                    "avg_visits": multi_asset_root_values[f"visits_template_{suffix}"].mean(),
                }
            )
        multi_asset_root_summary = pd.DataFrame(rows).to_string(index=False)
    spy_edge_summary = "No SPY root edge diagnostics were supplied."
    if spy_edge_diagnostics is not None and not spy_edge_diagnostics.empty:
        spy_edge_summary = spy_edge_diagnostics[
            ["chosen_minus_previous", "best_minus_previous", "switched", "chose_best"]
        ].describe(include="all").to_string()
    multi_asset_edge_summary = "No MultiAsset root edge diagnostics were supplied."
    if multi_asset_edge_diagnostics is not None and not multi_asset_edge_diagnostics.empty:
        multi_asset_edge_summary = multi_asset_edge_diagnostics[
            ["chosen_minus_previous", "best_minus_previous", "switched", "chose_best"]
        ].describe(include="all").to_string()

    content = f"""# MCTS Diagnostics

## Why the first MCTS version likely lagged

- It sampled independent one-day returns by regime, so a five-day search path could lose the serial structure that trend and volatility regimes depend on.
- The drawdown penalty was high relative to the daily return scale, which encouraged defensive actions even in historically positive regimes.
- Rollouts were guided only by average single-day regime return and had no strong connection to the Regime Rule signal that performed well.
- The search used the full action grid every day, which increased switching and made the strategy pay more transaction costs.
- The original comparison was not fully fair: `Regime Rule` could rotate into TLT/GLD during risk-off regimes, while SPY-only MCTS could only choose SPY or cash.

The root-child selection now explicitly uses average value (`child.value / child.visits`). The previous code already did this, and the implementation keeps that behavior.

## Current MCTS config

```text
{config_frame.to_string(index=False)}
```

## Second-round changes

- MCTS defaults to a path sampler: it samples historical continuous SPY return paths from dates that share the current regime.
- The reward is simplified to return minus transaction cost, with a much smaller configurable risk penalty.
- A positive next-20-day regime expectation now creates an opportunity cost for low exposure.
- Regime Rule SPY exposure is used as a prior, and the action set defaults to positions within +/-25 percentage points of that prior.
- Position diagnostics, MCTS position curves, and regime-level MCTS positioning reports are written under `reports/`.
- Added `Regime Rule SPY/Cash` to compare SPY-only timing against SPY-only MCTS.
- Added `Market Attractor MCTS MultiAsset`, which chooses among five discrete SPY/TLT/GLD/cash templates.
- Added `mcts_root_values.csv` to inspect the root action values and visits each day.
- Widened `prior_band` and always includes the previous SPY position plus `50%` in the candidate set, so the search is no longer only a binary perturbation of the prior.
- Added a small configurable action-inertia threshold to avoid switching when the estimated root-value edge is tiny.
- MultiAsset rollout now heavily favors holding the current template, and MultiAsset emits template path/root-value diagnostics.
- Added root edge diagnostics for chosen-versus-previous and best-versus-previous actions.

## Prior-restricted versus full-grid MCTS

When `use_full_action_grid` is `false`, MCTS only evaluates positions inside `prior_position +/- prior_band`. This makes the search more stable and lowers action churn, but it can also inherit a bad prior. In this project that matters because the prior comes from Regime Rule's SPY leg: risk-off regimes have SPY prior `0`, even though the original Regime Rule may still earn return through TLT/GLD. Setting `use_full_action_grid: true` lets every day evaluate all SPY weights, but it also increases exploration and turnover.

## Root action value bias

The table below summarizes average root values and average visits by action. In prior-restricted mode, actions outside the prior band correctly show zero visits for many days, so a low-visit high/low action means "not evaluated under the configured prior", not necessarily "bad action".

This run used a {full_grid_state}. The highest average root value was action `{best_root_action}`, while low actions `0.0/0.25` were chosen on `{low_action_share:.2%}` of evaluated days. If high actions have better root values but low actions are frequently chosen, the evidence points toward prior/action-set restriction or regime labeling rather than a root-value function that is intrinsically biased toward cash.

```text
{root_summary.to_string(index=False)}
```

Chosen SPY-only MCTS action shares:

```text
{chosen_counts.to_string()}
```

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

## MultiAsset template diagnostics

```text
{multi_asset_summary}
```

MultiAsset root values:

```text
{multi_asset_root_summary}
```

## Root edge diagnostics

SPY-only root edges:

```text
{spy_edge_summary}
```

MultiAsset root edges:

```text
{multi_asset_edge_summary}
```
"""
    path.write_text(content, encoding="utf-8")
