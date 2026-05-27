# Experiment Matrix Report

This is a full-sample exploratory benchmark. It is intentionally not walk-forward yet.

## Leakage Review

- Leakage level: `exploratory_full_sample`
- Known look-ahead sources:
  - full-sample regime fit
  - full-sample future-return regime ranking
  - full-sample MCTS path sampling
- This does not block the current exploratory benchmark run.

## Acceptance Gate

- `spy_mcts_gate`: SPY-only MCTS versus Regime Rule SPY/Cash.
- `multi_asset_mcts_gate`: MultiAsset MCTS versus Regime Rule.
- `overall_gate`: combined result across both MCTS variants.
- `PASS`: beats the relevant benchmark on CAGR, Sharpe, max drawdown, and turnover.
- `WEAK PASS`: close to the relevant benchmark on CAGR, Sharpe, and drawdown.
- `FAIL`: not close enough to the relevant benchmark.

## Gate Counts

```text
              count
overall_gate       
FAIL              8
```

## Experiment Comparison Summary

```text
         experiment                                                                                    hypothesis                                       changed_variable baseline_experiment                                                       expected_result                                                             success_criteria spy_mcts_gate multi_asset_mcts_gate overall_gate  spy_mcts_cagr_delta_vs_buy_hold  spy_mcts_sharpe_delta_vs_buy_hold  spy_mcts_max_drawdown_delta_vs_buy_hold  spy_mcts_turnover_delta_vs_buy_hold  spy_mcts_cagr_delta_vs_regime_rule_spy_cash  spy_mcts_sharpe_delta_vs_regime_rule_spy_cash  spy_mcts_max_drawdown_delta_vs_regime_rule_spy_cash  spy_mcts_turnover_delta_vs_regime_rule_spy_cash  spy_mcts_cagr_delta_vs_regime_rule_multiasset  spy_mcts_sharpe_delta_vs_regime_rule_multiasset  spy_mcts_max_drawdown_delta_vs_regime_rule_multiasset  spy_mcts_turnover_delta_vs_regime_rule_multiasset  multi_asset_mcts_cagr_delta_vs_buy_hold  multi_asset_mcts_sharpe_delta_vs_buy_hold  multi_asset_mcts_max_drawdown_delta_vs_buy_hold  multi_asset_mcts_turnover_delta_vs_buy_hold  multi_asset_mcts_cagr_delta_vs_regime_rule_spy_cash  multi_asset_mcts_sharpe_delta_vs_regime_rule_spy_cash  multi_asset_mcts_max_drawdown_delta_vs_regime_rule_spy_cash  multi_asset_mcts_turnover_delta_vs_regime_rule_spy_cash  multi_asset_mcts_cagr_delta_vs_regime_rule_multiasset  multi_asset_mcts_sharpe_delta_vs_regime_rule_multiasset  multi_asset_mcts_max_drawdown_delta_vs_regime_rule_multiasset  multi_asset_mcts_turnover_delta_vs_regime_rule_multiasset
       benchmark_v1          Baseline settings provide the reference for all exploratory full-sample experiments.                                                   none        benchmark_v1          Establish stable benchmark metrics and diagnostic artifacts.                    MCTS is at least a WEAK PASS versus Regime Rule SPY/Cash.     WEAK PASS                  FAIL         FAIL                        -0.069039                          -0.161302                                 0.135973                             0.199018                                    -0.002866                                       0.074278                                             0.081991                                         0.163615                                      -0.064228                                        -0.190063                                               0.081991                                           0.127728                                -0.075061                                  -0.277022                                         0.034171                                     0.757153                                            -0.008887                                              -0.041442                                                    -0.019811                                                 0.721751                                              -0.070250                                                -0.305784                                                      -0.019811                                                   0.685863
 exp_prior_band_025                  A tighter prior band reduces turnover but may over-constrain SPY allocation.                                        mcts.prior_band        benchmark_v1 Turnover decreases relative to benchmark_v1 with limited Sharpe loss.     SPY MCTS turnover delta improves while gate remains WEAK PASS or better.     WEAK PASS                  FAIL         FAIL                        -0.069039                          -0.161302                                 0.135973                             0.199018                                    -0.002866                                       0.074278                                             0.081991                                         0.163615                                      -0.064228                                        -0.190063                                               0.081991                                           0.127728                                -0.075061                                  -0.277022                                         0.034171                                     0.757153                                            -0.008887                                              -0.041442                                                    -0.019811                                                 0.721751                                              -0.070250                                                -0.305784                                                      -0.019811                                                   0.685863
 exp_prior_band_050           A wider prior band allows enough exploration while still preserving prior guidance.                                        mcts.prior_band        benchmark_v1                    Similar or better MCTS Sharpe versus benchmark_v1.                                   SPY MCTS gate remains WEAK PASS or better.     WEAK PASS                  FAIL         FAIL                        -0.069039                          -0.161302                                 0.135973                             0.199018                                    -0.002866                                       0.074278                                             0.081991                                         0.163615                                      -0.064228                                        -0.190063                                               0.081991                                           0.127728                                -0.075061                                  -0.277022                                         0.034171                                     0.757153                                            -0.008887                                              -0.041442                                                    -0.019811                                                 0.721751                                              -0.070250                                                -0.305784                                                      -0.019811                                                   0.685863
exp_prior_full_grid       Full action grid improves decision quality by removing prior-induced action censorship.                              mcts.use_full_action_grid        benchmark_v1  Sharpe or CAGR improves without unacceptable drawdown deterioration.          SPY MCTS gate is PASS or improves Sharpe delta versus benchmark_v1.          FAIL                  FAIL         FAIL                        -0.082091                          -0.312845                                 0.032191                             0.332808                                    -0.015917                                      -0.077265                                            -0.021791                                         0.297405                                      -0.077280                                        -0.341606                                              -0.021791                                           0.261518                                -0.075061                                  -0.277022                                         0.034171                                     0.757153                                            -0.008887                                              -0.041442                                                    -0.019811                                                 0.721751                                              -0.070250                                                -0.305784                                                      -0.019811                                                   0.685863
    exp_reward_risk      Light risk and opportunity penalties improve risk-adjusted returns versus simple reward. mcts.drawdown_penalty and mcts.opportunity_cost_weight        benchmark_v1             Sharpe and max drawdown improve versus exp_reward_simple.               SPY MCTS Sharpe delta versus Regime Rule SPY/Cash is positive.     WEAK PASS                  FAIL         FAIL                        -0.069039                          -0.161302                                 0.135973                             0.199018                                    -0.002866                                       0.074278                                             0.081991                                         0.163615                                      -0.064228                                        -0.190063                                               0.081991                                           0.127728                                -0.075061                                  -0.277022                                         0.034171                                     0.757153                                            -0.008887                                              -0.041442                                                    -0.019811                                                 0.721751                                              -0.070250                                                -0.305784                                                      -0.019811                                                   0.685863
  exp_reward_simple Removing risk and opportunity penalties reveals whether reward penalties caused conservatism. mcts.drawdown_penalty and mcts.opportunity_cost_weight        benchmark_v1                          CAGR improves, possibly with worse drawdown.  SPY MCTS CAGR delta versus Regime Rule SPY/Cash improves without FAIL gate.     WEAK PASS                  FAIL         FAIL                        -0.066238                          -0.145482                                 0.022590                             0.196957                                    -0.000065                                       0.090099                                            -0.031392                                         0.161554                                      -0.061427                                        -0.174243                                              -0.031392                                           0.125667                                -0.064083                                  -0.198175                                         0.016833                                     0.759578                                             0.002091                                               0.037406                                                    -0.037149                                                 0.724176                                              -0.059272                                                -0.226936                                                      -0.037149                                                   0.688288
  exp_sampler_daily     Independent daily sampling underperforms path sampling because it loses serial structure.                                           mcts.sampler        benchmark_v1                              Lower Sharpe or CAGR than path sampling.                     Used as a negative/control comparison; no PASS required.     WEAK PASS                  FAIL         FAIL                        -0.076910                          -0.221478                                 0.120629                             0.200655                                    -0.010737                                       0.014103                                             0.066647                                         0.165252                                      -0.072099                                        -0.250239                                               0.066647                                           0.129365                                -0.075061                                  -0.277022                                         0.034171                                     0.757153                                            -0.008887                                              -0.041442                                                    -0.019811                                                 0.721751                                              -0.070250                                                -0.305784                                                      -0.019811                                                   0.685863
   exp_sampler_path           Path sampling preserves short-horizon return structure and improves MCTS decisions.                                           mcts.sampler        benchmark_v1                     Sharpe or CAGR improves versus exp_sampler_daily. SPY MCTS gate remains WEAK PASS or better and beats daily sampler on Sharpe.     WEAK PASS                  FAIL         FAIL                        -0.069039                          -0.161302                                 0.135973                             0.199018                                    -0.002866                                       0.074278                                             0.081991                                         0.163615                                      -0.064228                                        -0.190063                                               0.081991                                           0.127728                                -0.075061                                  -0.277022                                         0.034171                                     0.757153                                            -0.008887                                              -0.041442                                                    -0.019811                                                 0.721751                                              -0.070250                                                -0.305784                                                      -0.019811                                                   0.685863
```

## Best by Sharpe

```text
         experiment    strategy overall_gate  total_return     cagr   sharpe   calmar  max_drawdown  avg_daily_turnover
  exp_sampler_daily  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
    exp_reward_risk  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
  exp_reward_simple  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
 exp_prior_band_050  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
 exp_prior_band_025  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
exp_prior_full_grid  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
       benchmark_v1  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
   exp_sampler_path  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
   exp_sampler_path MA200 Trend         FAIL      3.904562 0.101891 0.907802 0.505435     -0.201590            0.019156
  exp_sampler_daily MA200 Trend         FAIL      3.904562 0.101891 0.907802 0.505435     -0.201590            0.019156
```

## Best by Calmar

```text
         experiment    strategy overall_gate  total_return     cagr   sharpe   calmar  max_drawdown  avg_daily_turnover
  exp_sampler_daily  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
    exp_reward_risk  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
  exp_reward_simple  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
 exp_prior_band_050  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
 exp_prior_band_025  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
exp_prior_full_grid  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
       benchmark_v1  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
   exp_sampler_path  Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
   exp_sampler_path MA200 Trend         FAIL      3.904562 0.101891 0.907802 0.505435     -0.201590            0.019156
  exp_sampler_daily MA200 Trend         FAIL      3.904562 0.101891 0.907802 0.505435     -0.201590            0.019156
```

## Best by Max Drawdown

```text
         experiment              strategy overall_gate  total_return     cagr   sharpe   calmar  max_drawdown  avg_daily_turnover
  exp_reward_simple            Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
       benchmark_v1            Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
   exp_sampler_path            Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
    exp_reward_risk            Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
  exp_sampler_daily            Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
exp_prior_full_grid            Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
 exp_prior_band_050            Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
 exp_prior_band_025            Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
 exp_prior_band_025 Market Attractor MCTS         FAIL      2.185766 0.073260 0.702688 0.364114     -0.201200            0.199260
    exp_reward_risk Market Attractor MCTS         FAIL      2.185766 0.073260 0.702688 0.364114     -0.201200            0.199260
```

## Lowest Turnover

```text
         experiment   strategy overall_gate  total_return     cagr   sharpe   calmar  max_drawdown  avg_daily_turnover
       benchmark_v1 Buy & Hold         FAIL      7.849908 0.142299 0.863989 0.422036     -0.337173            0.000242
  exp_sampler_daily Buy & Hold         FAIL      7.849908 0.142299 0.863989 0.422036     -0.337173            0.000242
   exp_sampler_path Buy & Hold         FAIL      7.849908 0.142299 0.863989 0.422036     -0.337173            0.000242
  exp_reward_simple Buy & Hold         FAIL      7.849908 0.142299 0.863989 0.422036     -0.337173            0.000242
 exp_prior_band_025 Buy & Hold         FAIL      7.849908 0.142299 0.863989 0.422036     -0.337173            0.000242
    exp_reward_risk Buy & Hold         FAIL      7.849908 0.142299 0.863989 0.422036     -0.337173            0.000242
exp_prior_full_grid Buy & Hold         FAIL      7.849908 0.142299 0.863989 0.422036     -0.337173            0.000242
 exp_prior_band_050 Buy & Hold         FAIL      7.849908 0.142299 0.863989 0.422036     -0.337173            0.000242
  exp_sampler_daily Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
  exp_reward_simple Vol Target         FAIL      3.642787 0.098209 0.973871 0.766671     -0.128098            0.017483
```

## Best SPY-only MCTS Experiment

```text
        experiment spy_mcts_gate  total_return    cagr   sharpe  max_drawdown  avg_daily_turnover  spy_mcts_cagr_delta_vs_regime_rule_spy_cash  spy_mcts_sharpe_delta_vs_regime_rule_spy_cash  spy_mcts_max_drawdown_delta_vs_regime_rule_spy_cash  spy_mcts_turnover_delta_vs_regime_rule_spy_cash
 exp_reward_simple     WEAK PASS      2.324790 0.07606 0.718508     -0.314583            0.197199                                    -0.000065                                       0.090099                                            -0.031392                                         0.161554
      benchmark_v1     WEAK PASS      2.185766 0.07326 0.702688     -0.201200            0.199260                                    -0.002866                                       0.074278                                             0.081991                                         0.163615
exp_prior_band_025     WEAK PASS      2.185766 0.07326 0.702688     -0.201200            0.199260                                    -0.002866                                       0.074278                                             0.081991                                         0.163615
exp_prior_band_050     WEAK PASS      2.185766 0.07326 0.702688     -0.201200            0.199260                                    -0.002866                                       0.074278                                             0.081991                                         0.163615
   exp_reward_risk     WEAK PASS      2.185766 0.07326 0.702688     -0.201200            0.199260                                    -0.002866                                       0.074278                                             0.081991                                         0.163615
```

## Best MultiAsset MCTS Experiment

```text
         experiment multi_asset_mcts_gate  total_return     cagr   sharpe  max_drawdown  avg_daily_turnover  multi_asset_mcts_cagr_delta_vs_regime_rule_multiasset  multi_asset_mcts_sharpe_delta_vs_regime_rule_multiasset  multi_asset_mcts_max_drawdown_delta_vs_regime_rule_multiasset  multi_asset_mcts_turnover_delta_vs_regime_rule_multiasset
  exp_reward_simple                  FAIL      2.435643 0.078216 0.665815     -0.320339            0.759821                                              -0.059272                                                -0.226936                                                      -0.037149                                                   0.688288
       benchmark_v1                  FAIL      1.905143 0.067238 0.586967     -0.303002            0.757396                                              -0.070250                                                -0.305784                                                      -0.019811                                                   0.685863
 exp_prior_band_025                  FAIL      1.905143 0.067238 0.586967     -0.303002            0.757396                                              -0.070250                                                -0.305784                                                      -0.019811                                                   0.685863
 exp_prior_band_050                  FAIL      1.905143 0.067238 0.586967     -0.303002            0.757396                                              -0.070250                                                -0.305784                                                      -0.019811                                                   0.685863
exp_prior_full_grid                  FAIL      1.905143 0.067238 0.586967     -0.303002            0.757396                                              -0.070250                                                -0.305784                                                      -0.019811                                                   0.685863
```

## Next Recommended Experiments

- Promote or retest the strongest SPY-only candidate: exp_reward_simple (WEAK PASS).
- Use multi-asset results as diagnostics until a candidate improves versus Regime Rule: current best is exp_reward_simple (FAIL).
- Investigate FAIL experiments before expanding the matrix.
- Keep walk-forward validation out of this benchmark until full-sample experiments stabilize.

## Required Artifacts

Each experiment directory contains `config_snapshot.yaml`, `metrics.csv`, `equity_curve.csv`, `drawdown.csv`, `strategy_diagnostics.csv`, `mcts_root_values.csv`, and `review.json`.
