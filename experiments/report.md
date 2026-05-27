# Experiment Matrix Report

This is a full-sample exploratory benchmark. It is intentionally not walk-forward yet.

## Acceptance Gate

- `PASS`: MCTS beats Regime Rule SPY/Cash on CAGR, Sharpe, max drawdown, and turnover.
- `WEAK PASS`: MCTS is close to Regime Rule SPY/Cash on CAGR/Sharpe/drawdown.
- `FAIL`: MCTS is not close enough to the SPY-only regime benchmark.

## Gate Counts

```text
                 count
acceptance_gate       
WEAK PASS            7
FAIL                 1
```

## Experiment Comparison Summary

```text
         experiment acceptance_gate  mcts_cagr_delta_vs_buy_hold  mcts_sharpe_delta_vs_buy_hold  mcts_max_drawdown_delta_vs_buy_hold  mcts_turnover_delta_vs_buy_hold  mcts_cagr_delta_vs_regime_rule_spy_cash  mcts_sharpe_delta_vs_regime_rule_spy_cash  mcts_max_drawdown_delta_vs_regime_rule_spy_cash  mcts_turnover_delta_vs_regime_rule_spy_cash  mcts_cagr_delta_vs_regime_rule_multiasset  mcts_sharpe_delta_vs_regime_rule_multiasset  mcts_max_drawdown_delta_vs_regime_rule_multiasset  mcts_turnover_delta_vs_regime_rule_multiasset
       benchmark_v1       WEAK PASS                    -0.069039                      -0.161302                             0.135973                         0.199018                                -0.002866                                   0.074278                                         0.081991                                     0.163615                                  -0.064228                                    -0.190063                                           0.081991                                       0.127728
 exp_prior_band_025       WEAK PASS                    -0.069039                      -0.161302                             0.135973                         0.199018                                -0.002866                                   0.074278                                         0.081991                                     0.163615                                  -0.064228                                    -0.190063                                           0.081991                                       0.127728
 exp_prior_band_050       WEAK PASS                    -0.069039                      -0.161302                             0.135973                         0.199018                                -0.002866                                   0.074278                                         0.081991                                     0.163615                                  -0.064228                                    -0.190063                                           0.081991                                       0.127728
exp_prior_full_grid            FAIL                    -0.082091                      -0.312845                             0.032191                         0.332808                                -0.015917                                  -0.077265                                        -0.021791                                     0.297405                                  -0.077280                                    -0.341606                                          -0.021791                                       0.261518
    exp_reward_risk       WEAK PASS                    -0.069039                      -0.161302                             0.135973                         0.199018                                -0.002866                                   0.074278                                         0.081991                                     0.163615                                  -0.064228                                    -0.190063                                           0.081991                                       0.127728
  exp_reward_simple       WEAK PASS                    -0.066238                      -0.145482                             0.022590                         0.196957                                -0.000065                                   0.090099                                        -0.031392                                     0.161554                                  -0.061427                                    -0.174243                                          -0.031392                                       0.125667
  exp_sampler_daily       WEAK PASS                    -0.076910                      -0.221478                             0.120629                         0.200655                                -0.010737                                   0.014103                                         0.066647                                     0.165252                                  -0.072099                                    -0.250239                                           0.066647                                       0.129365
   exp_sampler_path       WEAK PASS                    -0.069039                      -0.161302                             0.135973                         0.199018                                -0.002866                                   0.074278                                         0.081991                                     0.163615                                  -0.064228                                    -0.190063                                           0.081991                                       0.127728
```

## MCTS Strategy Rows

```text
         experiment acceptance_gate  total_return     cagr   sharpe  max_drawdown  avg_daily_turnover  mcts_cagr_delta_vs_regime_rule_spy_cash  mcts_sharpe_delta_vs_regime_rule_spy_cash  mcts_max_drawdown_delta_vs_regime_rule_spy_cash  mcts_turnover_delta_vs_regime_rule_spy_cash
exp_prior_full_grid            FAIL      1.606933 0.060208 0.551145     -0.304982            0.333050                                -0.015917                                  -0.077265                                        -0.021791                                     0.297405
  exp_reward_simple       WEAK PASS      2.324790 0.076060 0.718508     -0.314583            0.197199                                -0.000065                                   0.090099                                        -0.031392                                     0.161554
       benchmark_v1       WEAK PASS      2.185766 0.073260 0.702688     -0.201200            0.199260                                -0.002866                                   0.074278                                         0.081991                                     0.163615
 exp_prior_band_025       WEAK PASS      2.185766 0.073260 0.702688     -0.201200            0.199260                                -0.002866                                   0.074278                                         0.081991                                     0.163615
 exp_prior_band_050       WEAK PASS      2.185766 0.073260 0.702688     -0.201200            0.199260                                -0.002866                                   0.074278                                         0.081991                                     0.163615
    exp_reward_risk       WEAK PASS      2.185766 0.073260 0.702688     -0.201200            0.199260                                -0.002866                                   0.074278                                         0.081991                                     0.163615
   exp_sampler_path       WEAK PASS      2.185766 0.073260 0.702688     -0.201200            0.199260                                -0.002866                                   0.074278                                         0.081991                                     0.163615
  exp_sampler_daily       WEAK PASS      1.823727 0.065389 0.642512     -0.216544            0.200897                                -0.010737                                   0.014103                                         0.066647                                     0.165252
```

## Required Artifacts

Each experiment directory contains `config_snapshot.yaml`, `metrics.csv`, `equity_curve.csv`, `drawdown.csv`, `strategy_diagnostics.csv`, and `mcts_root_values.csv`.
