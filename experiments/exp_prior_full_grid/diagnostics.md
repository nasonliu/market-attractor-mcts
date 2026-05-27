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
                             horizon                           5
                 simulations_per_day                         100
                exploration_constant                    1.414214
                             sampler                        path
                use_full_action_grid                        True
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

This run used a full action grid. The highest average root value was action `0.0`, while low actions `0.0/0.25` were chosen on `22.50%` of evaluated days. If high actions have better root values but low actions are frequently chosen, the evidence points toward prior/action-set restriction or regime labeling rather than a root-value function that is intrinsically biased toward cash.

```text
 action  avg_root_value  avg_visits
   0.00       -0.000718   20.017580
   0.25       -0.000794   20.012739
   0.50       -0.000944   20.004076
   0.75       -0.001195   19.978089
   1.00       -0.001091   19.987516
```

Chosen SPY-only MCTS action shares:

```text
                 chosen_share
chosen_position              
0.00                 0.096306
0.25                 0.128662
0.50                 0.192102
0.75                 0.261401
1.00                 0.321529
```

## Latest metrics

```text
                        strategy  total_return     cagr  annual_vol   sharpe  max_drawdown   calmar  daily_win_rate  avg_daily_turnover
                      Buy & Hold      7.849908 0.142299    0.171266 0.863989     -0.337173 0.422036        0.553589            0.000242
                     MA200 Trend      3.904562 0.101891    0.114273 0.907802     -0.201590 0.505435        0.448351            0.019156
                      Vol Target      3.642787 0.098209    0.101670 0.973871     -0.128098 0.766671        0.550679            0.017483
                     Regime Rule      7.258470 0.137488    0.158667 0.892751     -0.283190 0.485496        0.548982            0.071532
            Regime Rule SPY/Cash      2.328073 0.076125    0.130513 0.628409     -0.283190 0.268813        0.194714            0.035645
           Market Attractor MCTS      1.606933 0.060208    0.119194 0.551145     -0.304982 0.197416        0.467265            0.333050
Market Attractor MCTS MultiAsset      1.905143 0.067238    0.124175 0.586967     -0.303002 0.221906        0.459505            0.757396
```

## Strategy position diagnostics

```text
                        strategy  avg_position  annualized_turnover  min_position  max_position  position_0pct_days  position_25pct_days  position_50pct_days  position_75pct_days  position_100pct_days
                      Buy & Hold      1.000000             0.000000           1.0           1.0            0.000000             0.000000             0.000000             0.000000              1.000000
                     MA200 Trend      0.805529             4.827352           0.0           1.0            0.194471             0.000000             0.000000             0.000000              0.805529
                      Vol Target      0.758327             4.407098           0.0           1.0            0.004850             0.000000             0.000242             0.000000              0.315713
                     Regime Rule      0.344083            17.965082           0.0           1.0            0.655917             0.000000             0.000000             0.000000              0.344083
            Regime Rule SPY/Cash      0.344083             8.982541           0.0           1.0            0.655917             0.000000             0.000000             0.000000              0.344083
           Market Attractor MCTS      0.614634            83.959263           0.0           1.0            0.139913             0.122454             0.182832             0.248788              0.306014
Market Attractor MCTS MultiAsset      0.505335           190.894277           0.0           1.0            0.354510             0.000000             0.178468             0.203686              0.263337
```

## MCTS by regime

```text
 regime  mcts_avg_position  regime_rule_position  next_5d_return  next_20d_return
    0.0           0.656921                   1.0        0.004370         0.014662
    1.0           0.634250                   0.0        0.001007         0.004116
    2.0           0.655615                   0.0        0.003668         0.013833
    3.0           0.640374                   1.0        0.004396         0.022933
```

## MultiAsset template diagnostics

```text
Daily template transition rate: 73.58%

                             template_share
template_name                              
100% SPY                           0.276688
50% TLT + 50% GLD                  0.219363
75% SPY + 25% TLT                  0.214013
50% SPY + 25% TLT + 25% GLD        0.187516
100% cash                          0.102420
```

MultiAsset root values:

```text
 template  avg_root_value  avg_visits
        0       -0.000846   20.002803
        1       -0.000829   20.005096
        2       -0.000658   20.007134
        3       -0.001534   19.967643
        4       -0.000423   20.017325
```

## Root edge diagnostics

SPY-only root edges:

```text
        chosen_minus_previous  best_minus_previous switched chose_best
count             3925.000000          3925.000000     3925       3925
unique                    NaN                  NaN        2          2
top                       NaN                  NaN     True       True
freq                      NaN                  NaN     2945       3848
mean                 0.008405             0.008409      NaN        NaN
std                  0.010727             0.010724      NaN        NaN
min                  0.000000             0.000000      NaN        NaN
25%                  0.000511             0.000511      NaN        NaN
50%                  0.005451             0.005451      NaN        NaN
75%                  0.011778             0.011778      NaN        NaN
max                  0.107092             0.107092      NaN        NaN
```

MultiAsset root edges:

```text
        chosen_minus_previous  best_minus_previous switched chose_best
count             3925.000000          3925.000000     3925       3925
unique                    NaN                  NaN        2          2
top                       NaN                  NaN     True       True
freq                      NaN                  NaN     2888       3776
mean                 0.009408             0.009428      NaN        NaN
std                  0.011051             0.011035      NaN        NaN
min                  0.000000             0.000000      NaN        NaN
25%                  0.000000             0.000667      NaN        NaN
50%                  0.006673             0.006673      NaN        NaN
75%                  0.013525             0.013525      NaN        NaN
max                  0.104953             0.104953      NaN        NaN
```
