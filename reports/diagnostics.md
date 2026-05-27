# MCTS Diagnostics

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
             strategy  total_return     cagr  annual_vol   sharpe  max_drawdown   calmar  daily_win_rate  avg_daily_turnover
           Buy & Hold      7.849908 0.142299    0.171266 0.863989     -0.337173 0.422036        0.553589            0.000242
          MA200 Trend      3.904562 0.101891    0.114273 0.907802     -0.201590 0.505435        0.448351            0.019156
           Vol Target      3.642787 0.098209    0.101670 0.973871     -0.128098 0.766671        0.550679            0.017483
          Regime Rule      7.258470 0.137488    0.158667 0.892751     -0.283190 0.485496        0.548982            0.071532
Market Attractor MCTS      1.860642 0.066233    0.117079 0.607289     -0.264585 0.250329        0.362027            0.138094
```

## Strategy position diagnostics

```text
             strategy  avg_position  annualized_turnover  min_position  max_position  position_0pct_days  position_25pct_days  position_50pct_days  position_75pct_days  position_100pct_days
           Buy & Hold      1.000000             0.000000           1.0           1.0            0.000000             0.000000             0.000000             0.000000              1.000000
          MA200 Trend      0.805529             4.827352           0.0           1.0            0.194471             0.000000             0.000000             0.000000              0.805529
           Vol Target      0.758327             4.407098           0.0           1.0            0.004850             0.000000             0.000242             0.000000              0.315713
          Regime Rule      0.344083            17.965082           0.0           1.0            0.655917             0.000000             0.000000             0.000000              0.344083
Market Attractor MCTS      0.381244            34.799709           0.0           1.0            0.341659             0.314258             0.000000             0.165616              0.178468
```

## MCTS by regime

```text
 regime  mcts_avg_position  regime_rule_position  next_5d_return  next_20d_return
    0.0           0.878878                   1.0        0.004370         0.014662
    1.0           0.134420                   0.0        0.001007         0.004116
    2.0           0.121975                   0.0        0.003668         0.013833
    3.0           0.879234                   1.0        0.004396         0.022933
```
