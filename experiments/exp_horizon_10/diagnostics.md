# MCTS Diagnostics

## Why the first MCTS version likely lagged

- It sampled independent one-day returns by regime, so a five-day search path could lose the serial structure that trend and volatility regimes depend on.
- The drawdown penalty was high relative to the daily return scale, which encouraged defensive actions even in historically positive regimes.
- Rollouts were guided only by average single-day regime return and had no strong connection to the Regime Rule signal that performed well.
- The search used the full action grid every day, which increased switching and made the strategy pay more transaction costs.
- The original comparison was not fully fair: `Regime Rule` could rotate into TLT/GLD during risk-off regimes, while SPY-only MCTS could only choose SPY or cash.

The root-child selection now explicitly uses average value (`child.value / child.visits`). The previous code already did this, and the implementation keeps that behavior.

## Current MCTS config

```text
                           parameter                       value
                               asset                         SPY
                           positions [0.0, 0.25, 0.5, 0.75, 1.0]
                             horizon                          10
                 simulations_per_day                         100
                exploration_constant                    1.414214
                             sampler                        path
                use_full_action_grid                       False
                          prior_band                         0.5
                    drawdown_penalty                         0.1
             opportunity_cost_weight                         0.2
            action_inertia_threshold                      0.0005
       multi_asset_hold_rollout_prob                        0.95
multi_asset_action_inertia_threshold                       0.001
                transaction_cost_bps                         2.0
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

This run used a prior-restricted grid with prior_band=0.5. The highest average root value was action `0.0`, while low actions `0.0/0.25` were chosen on `37.99%` of evaluated days. If high actions have better root values but low actions are frequently chosen, the evidence points toward prior/action-set restriction or regime labeling rather than a root-value function that is intrinsically biased toward cash.

```text
 action  avg_root_value  avg_visits
   0.00       -0.002267   21.243057
   0.25       -0.002382   21.297580
   0.50       -0.002632   33.086879
   0.75       -0.002402   12.198726
   1.00       -0.003003   12.173758
```

Chosen SPY-only MCTS action shares:

```text
                 chosen_share
chosen_position              
0.00                 0.175032
0.25                 0.204841
0.50                 0.365860
0.75                 0.118471
1.00                 0.135796
```

## Latest metrics

```text
                        strategy  total_return     cagr  annual_vol   sharpe  max_drawdown   calmar  daily_win_rate  avg_daily_turnover
                      Buy & Hold      7.849912 0.142299    0.171266 0.863989     -0.337173 0.422035        0.553589            0.000242
                     MA200 Trend      3.904566 0.101891    0.114273 0.907802     -0.201591 0.505435        0.448351            0.019156
                      Vol Target      3.642770 0.098209    0.101670 0.973869     -0.128099 0.766667        0.550679            0.017483
                     Regime Rule      7.258468 0.137488    0.158667 0.892750     -0.283190 0.485497        0.548982            0.071532
            Regime Rule SPY/Cash      2.328077 0.076125    0.130513 0.628409     -0.283190 0.268813        0.194714            0.035645
           Market Attractor MCTS      2.628866 0.081822    0.108547 0.780111     -0.223654 0.365842        0.437197            0.205141
Market Attractor MCTS MultiAsset      0.870095 0.038935    0.121703 0.375300     -0.244759 0.159075        0.434772            0.767338
```

## Strategy position diagnostics

```text
                        strategy  avg_position  annualized_turnover  min_position  max_position  position_0pct_days  position_25pct_days  position_50pct_days  position_75pct_days  position_100pct_days
                      Buy & Hold      1.000000             0.000000           1.0           1.0            0.000000             0.000000             0.000000             0.000000              1.000000
                     MA200 Trend      0.805529             4.827352           0.0           1.0            0.194471             0.000000             0.000000             0.000000              0.805529
                      Vol Target      0.758327             4.407099           0.0           1.0            0.004850             0.000000             0.000242             0.000000              0.315713
                     Regime Rule      0.344083            17.965082           0.0           1.0            0.655917             0.000000             0.000000             0.000000              0.344083
            Regime Rule SPY/Cash      0.344083             8.982541           0.0           1.0            0.655917             0.000000             0.000000             0.000000              0.344083
           Market Attractor MCTS      0.436651            51.725994           0.0           1.0            0.214840             0.194956             0.348206             0.112755              0.129243
Market Attractor MCTS MultiAsset      0.485269           193.430165           0.0           1.0            0.373424             0.000000             0.180407             0.204413              0.241756
```

## MCTS by regime

```text
 regime  mcts_avg_position  regime_rule_position  next_5d_return  next_20d_return
    0.0           0.767900                   1.0        0.004370         0.014662
    1.0           0.286490                   0.0        0.001007         0.004116
    2.0           0.287270                   0.0        0.003668         0.013833
    3.0           0.755348                   1.0        0.004396         0.022933
```

## MultiAsset template diagnostics

```text
Daily template transition rate: 75.59%

                             template_share
template_name                              
100% SPY                           0.254013
75% SPY + 25% TLT                  0.214777
50% TLT + 50% GLD                  0.202038
50% SPY + 25% TLT + 25% GLD        0.189554
100% cash                          0.139618
```

MultiAsset root values:

```text
 template  avg_root_value  avg_visits
        0       -0.004517   19.964841
        1       -0.003623   20.012739
        2       -0.003496   20.015796
        3       -0.004847   19.951338
        4       -0.002823   20.055287
```

## Root edge diagnostics

SPY-only root edges:

```text
        chosen_minus_previous  best_minus_previous switched chose_best
count             3925.000000          3925.000000     3925       3925
unique                    NaN                  NaN        2          2
top                       NaN                  NaN     True       True
freq                      NaN                  NaN     2478       3793
mean                 0.006630             0.006639      NaN        NaN
std                  0.012526             0.012521      NaN        NaN
min                  0.000000             0.000000      NaN        NaN
25%                  0.000000             0.000000      NaN        NaN
50%                  0.002402             0.002402      NaN        NaN
75%                  0.007765             0.007765      NaN        NaN
max                  0.215869             0.215869      NaN        NaN
```

MultiAsset root edges:

```text
        chosen_minus_previous  best_minus_previous switched chose_best
count             3925.000000          3925.000000     3925       3925
unique                    NaN                  NaN        2          2
top                       NaN                  NaN     True       True
freq                      NaN                  NaN     2967       3815
mean                 0.011651             0.011665      NaN        NaN
std                  0.013521             0.013509      NaN        NaN
min                  0.000000             0.000000      NaN        NaN
25%                  0.001179             0.001179      NaN        NaN
50%                  0.008084             0.008084      NaN        NaN
75%                  0.016650             0.016650      NaN        NaN
max                  0.138144             0.138144      NaN        NaN
```
