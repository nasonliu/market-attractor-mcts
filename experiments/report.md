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
         experiment                                                                                    hypothesis                                       changed_variable baseline_experiment                                                       expected_result                                                             success_criteria spy_mcts_gate multi_asset_mcts_gate overall_gate hypothesis_supported         decision          primary_failure_mode                                                               next_recommended_experiment           leakage_level  contract_review_passed  spy_mcts_cagr_delta_vs_buy_hold  spy_mcts_sharpe_delta_vs_buy_hold  spy_mcts_calmar_delta_vs_buy_hold  spy_mcts_max_drawdown_delta_vs_buy_hold  spy_mcts_turnover_delta_vs_buy_hold  spy_mcts_cagr_delta_vs_regime_rule_spy_cash  spy_mcts_sharpe_delta_vs_regime_rule_spy_cash  spy_mcts_calmar_delta_vs_regime_rule_spy_cash  spy_mcts_max_drawdown_delta_vs_regime_rule_spy_cash  spy_mcts_turnover_delta_vs_regime_rule_spy_cash  spy_mcts_cagr_delta_vs_regime_rule_multiasset  spy_mcts_sharpe_delta_vs_regime_rule_multiasset  spy_mcts_calmar_delta_vs_regime_rule_multiasset  spy_mcts_max_drawdown_delta_vs_regime_rule_multiasset  spy_mcts_turnover_delta_vs_regime_rule_multiasset  multi_asset_mcts_cagr_delta_vs_buy_hold  multi_asset_mcts_sharpe_delta_vs_buy_hold  multi_asset_mcts_calmar_delta_vs_buy_hold  multi_asset_mcts_max_drawdown_delta_vs_buy_hold  multi_asset_mcts_turnover_delta_vs_buy_hold  multi_asset_mcts_cagr_delta_vs_regime_rule_spy_cash  multi_asset_mcts_sharpe_delta_vs_regime_rule_spy_cash  multi_asset_mcts_calmar_delta_vs_regime_rule_spy_cash  multi_asset_mcts_max_drawdown_delta_vs_regime_rule_spy_cash  multi_asset_mcts_turnover_delta_vs_regime_rule_spy_cash  multi_asset_mcts_cagr_delta_vs_regime_rule_multiasset  multi_asset_mcts_sharpe_delta_vs_regime_rule_multiasset  multi_asset_mcts_calmar_delta_vs_regime_rule_multiasset  multi_asset_mcts_max_drawdown_delta_vs_regime_rule_multiasset  multi_asset_mcts_turnover_delta_vs_regime_rule_multiasset
       benchmark_v1          Baseline settings provide the reference for all exploratory full-sample experiments.                                                   none        benchmark_v1          Establish stable benchmark metrics and diagnostic artifacts.                    MCTS is at least a WEAK PASS versus Regime Rule SPY/Cash.     WEAK PASS                  FAIL         FAIL         inconclusive KEEP_EXPLORATORY multi_asset_turnover_too_high Test MultiAsset template persistence or turnover damping in a single-variable experiment. exploratory_full_sample                    True                        -0.075831                          -0.210311                          -0.167130                                 0.076417                             0.202534                                    -0.009657                                       0.025269                                      -0.013908                                             0.022434                                         0.167131                                      -0.071020                                        -0.239072                                        -0.230592                                               0.022434                                           0.131244                                -0.075489                                  -0.280265                                  -0.201540                                         0.034172                                     0.757032                                            -0.009315                                              -0.044685                                              -0.048318                                                    -0.019810                                                 0.721629                                              -0.070678                                                -0.309026                                                -0.265002                                                      -0.019810                                                   0.685742
 exp_prior_band_025                  A tighter prior band reduces turnover but may over-constrain SPY allocation.                                        mcts.prior_band        benchmark_v1 Turnover decreases relative to benchmark_v1 with limited Sharpe loss.     SPY MCTS turnover delta improves while gate remains WEAK PASS or better.     WEAK PASS                  FAIL         FAIL                 True KEEP_EXPLORATORY multi_asset_turnover_too_high Test MultiAsset template persistence or turnover damping in a single-variable experiment. exploratory_full_sample                    True                        -0.075831                          -0.210311                          -0.167130                                 0.076417                             0.202534                                    -0.009657                                       0.025269                                      -0.013908                                             0.022434                                         0.167131                                      -0.071020                                        -0.239072                                        -0.230592                                               0.022434                                           0.131244                                -0.075489                                  -0.280265                                  -0.201540                                         0.034172                                     0.757032                                            -0.009315                                              -0.044685                                              -0.048318                                                    -0.019810                                                 0.721629                                              -0.070678                                                -0.309026                                                -0.265002                                                      -0.019810                                                   0.685742
 exp_prior_band_050           A wider prior band allows enough exploration while still preserving prior guidance.                                        mcts.prior_band        benchmark_v1                    Similar or better MCTS Sharpe versus benchmark_v1.                                   SPY MCTS gate remains WEAK PASS or better.     WEAK PASS                  FAIL         FAIL                 True KEEP_EXPLORATORY multi_asset_turnover_too_high Test MultiAsset template persistence or turnover damping in a single-variable experiment. exploratory_full_sample                    True                        -0.075831                          -0.210311                          -0.167130                                 0.076417                             0.202534                                    -0.009657                                       0.025269                                      -0.013908                                             0.022434                                         0.167131                                      -0.071020                                        -0.239072                                        -0.230592                                               0.022434                                           0.131244                                -0.075489                                  -0.280265                                  -0.201540                                         0.034172                                     0.757032                                            -0.009315                                              -0.044685                                              -0.048318                                                    -0.019810                                                 0.721629                                              -0.070678                                                -0.309026                                                -0.265002                                                      -0.019810                                                   0.685742
exp_prior_full_grid       Full action grid improves decision quality by removing prior-induced action censorship.                              mcts.use_full_action_grid        benchmark_v1  Sharpe or CAGR improves without unacceptable drawdown deterioration.          SPY MCTS gate is PASS or improves Sharpe delta versus benchmark_v1.          FAIL                  FAIL         FAIL                False           REJECT multi_asset_turnover_too_high Test MultiAsset template persistence or turnover damping in a single-variable experiment. exploratory_full_sample                    True                        -0.082116                          -0.313047                          -0.224703                                 0.032191                             0.332444                                    -0.015943                                      -0.077467                                      -0.071481                                            -0.021791                                         0.297042                                      -0.077305                                        -0.341808                                        -0.288164                                              -0.021791                                           0.261154                                -0.075489                                  -0.280265                                  -0.201540                                         0.034172                                     0.757032                                            -0.009315                                              -0.044685                                              -0.048318                                                    -0.019810                                                 0.721629                                              -0.070678                                                -0.309026                                                -0.265002                                                      -0.019810                                                   0.685742
    exp_reward_risk      Light risk and opportunity penalties improve risk-adjusted returns versus simple reward. mcts.drawdown_penalty and mcts.opportunity_cost_weight        benchmark_v1             Sharpe and max drawdown improve versus exp_reward_simple.               SPY MCTS Sharpe delta versus Regime Rule SPY/Cash is positive.     WEAK PASS                  FAIL         FAIL                 True KEEP_EXPLORATORY multi_asset_turnover_too_high Test MultiAsset template persistence or turnover damping in a single-variable experiment. exploratory_full_sample                    True                        -0.075831                          -0.210311                          -0.167130                                 0.076417                             0.202534                                    -0.009657                                       0.025269                                      -0.013908                                             0.022434                                         0.167131                                      -0.071020                                        -0.239072                                        -0.230592                                               0.022434                                           0.131244                                -0.075489                                  -0.280265                                  -0.201540                                         0.034172                                     0.757032                                            -0.009315                                              -0.044685                                              -0.048318                                                    -0.019810                                                 0.721629                                              -0.070678                                                -0.309026                                                -0.265002                                                      -0.019810                                                   0.685742
  exp_reward_simple Removing risk and opportunity penalties reveals whether reward penalties caused conservatism. mcts.drawdown_penalty and mcts.opportunity_cost_weight        benchmark_v1                          CAGR improves, possibly with worse drawdown.  SPY MCTS CAGR delta versus Regime Rule SPY/Cash improves without FAIL gate.     WEAK PASS                  FAIL         FAIL                 True KEEP_EXPLORATORY multi_asset_turnover_too_high Test MultiAsset template persistence or turnover damping in a single-variable experiment. exploratory_full_sample                    True                        -0.066268                          -0.145731                          -0.180347                                 0.022590                             0.196957                                    -0.000094                                       0.089849                                      -0.027125                                            -0.031393                                         0.161554                                      -0.061457                                        -0.174492                                        -0.243808                                              -0.031393                                           0.125667                                -0.064083                                  -0.198174                                  -0.177869                                         0.016833                                     0.759578                                             0.002091                                               0.037406                                              -0.024647                                                    -0.037149                                                 0.724176                                              -0.059272                                                -0.226935                                                -0.241330                                                      -0.037149                                                   0.688288
  exp_sampler_daily     Independent daily sampling underperforms path sampling because it loses serial structure.                                           mcts.sampler        benchmark_v1                              Lower Sharpe or CAGR than path sampling.                     Used as a negative/control comparison; no PASS required.     WEAK PASS                  FAIL         FAIL                 True KEEP_EXPLORATORY multi_asset_turnover_too_high Test MultiAsset template persistence or turnover damping in a single-variable experiment. exploratory_full_sample                    True                        -0.076995                          -0.221641                          -0.120463                                 0.120629                             0.199200                                    -0.010822                                       0.013939                                       0.032759                                             0.066646                                         0.163797                                      -0.072184                                        -0.250402                                        -0.183924                                               0.066646                                           0.127910                                -0.075489                                  -0.280265                                  -0.201540                                         0.034172                                     0.757032                                            -0.009315                                              -0.044685                                              -0.048318                                                    -0.019810                                                 0.721629                                              -0.070678                                                -0.309026                                                -0.265002                                                      -0.019810                                                   0.685742
   exp_sampler_path           Path sampling preserves short-horizon return structure and improves MCTS decisions.                                           mcts.sampler        benchmark_v1                     Sharpe or CAGR improves versus exp_sampler_daily. SPY MCTS gate remains WEAK PASS or better and beats daily sampler on Sharpe.     WEAK PASS                  FAIL         FAIL                 True KEEP_EXPLORATORY multi_asset_turnover_too_high Test MultiAsset template persistence or turnover damping in a single-variable experiment. exploratory_full_sample                    True                        -0.075831                          -0.210311                          -0.167130                                 0.076417                             0.202534                                    -0.009657                                       0.025269                                      -0.013908                                             0.022434                                         0.167131                                      -0.071020                                        -0.239072                                        -0.230592                                               0.022434                                           0.131244                                -0.075489                                  -0.280265                                  -0.201540                                         0.034172                                     0.757032                                            -0.009315                                              -0.044685                                              -0.048318                                                    -0.019810                                                 0.721629                                              -0.070678                                                -0.309026                                                -0.265002                                                      -0.019810                                                   0.685742
```

## Best by Sharpe

```text
         experiment    strategy overall_gate  total_return     cagr   sharpe   calmar  max_drawdown  avg_daily_turnover
    exp_reward_risk  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
  exp_sampler_daily  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
   exp_sampler_path  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
  exp_reward_simple  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
exp_prior_full_grid  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
 exp_prior_band_025  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
 exp_prior_band_050  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
       benchmark_v1  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
    exp_reward_risk MA200 Trend         FAIL      3.904566 0.101891 0.907802 0.505435     -0.201591            0.019156
  exp_reward_simple MA200 Trend         FAIL      3.904566 0.101891 0.907802 0.505435     -0.201591            0.019156
```

## Best by Calmar

```text
         experiment    strategy overall_gate  total_return     cagr   sharpe   calmar  max_drawdown  avg_daily_turnover
  exp_sampler_daily  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
    exp_reward_risk  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
  exp_reward_simple  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
 exp_prior_band_050  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
 exp_prior_band_025  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
exp_prior_full_grid  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
   exp_sampler_path  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
       benchmark_v1  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
       benchmark_v1 MA200 Trend         FAIL      3.904566 0.101891 0.907802 0.505435     -0.201591            0.019156
   exp_sampler_path MA200 Trend         FAIL      3.904566 0.101891 0.907802 0.505435     -0.201591            0.019156
```

## Best by Max Drawdown

```text
         experiment    strategy overall_gate  total_return     cagr   sharpe   calmar  max_drawdown  avg_daily_turnover
  exp_reward_simple  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
    exp_reward_risk  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
  exp_sampler_daily  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
 exp_prior_band_050  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
 exp_prior_band_025  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
   exp_sampler_path  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
exp_prior_full_grid  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
       benchmark_v1  Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
       benchmark_v1 MA200 Trend         FAIL      3.904566 0.101891 0.907802 0.505435     -0.201591            0.019156
 exp_prior_band_025 MA200 Trend         FAIL      3.904566 0.101891 0.907802 0.505435     -0.201591            0.019156
```

## Lowest Turnover

```text
         experiment   strategy overall_gate  total_return     cagr   sharpe   calmar  max_drawdown  avg_daily_turnover
       benchmark_v1 Buy & Hold         FAIL      7.849912 0.142299 0.863989 0.422035     -0.337173            0.000242
  exp_sampler_daily Buy & Hold         FAIL      7.849912 0.142299 0.863989 0.422035     -0.337173            0.000242
   exp_sampler_path Buy & Hold         FAIL      7.849912 0.142299 0.863989 0.422035     -0.337173            0.000242
  exp_reward_simple Buy & Hold         FAIL      7.849912 0.142299 0.863989 0.422035     -0.337173            0.000242
 exp_prior_band_025 Buy & Hold         FAIL      7.849912 0.142299 0.863989 0.422035     -0.337173            0.000242
    exp_reward_risk Buy & Hold         FAIL      7.849912 0.142299 0.863989 0.422035     -0.337173            0.000242
exp_prior_full_grid Buy & Hold         FAIL      7.849912 0.142299 0.863989 0.422035     -0.337173            0.000242
 exp_prior_band_050 Buy & Hold         FAIL      7.849912 0.142299 0.863989 0.422035     -0.337173            0.000242
  exp_sampler_daily Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
  exp_reward_simple Vol Target         FAIL      3.642770 0.098209 0.973869 0.766667     -0.128099            0.017483
```

## Best SPY-only MCTS Experiment

```text
        experiment spy_mcts_gate  total_return     cagr   sharpe  max_drawdown  avg_daily_turnover  spy_mcts_cagr_delta_vs_regime_rule_spy_cash  spy_mcts_sharpe_delta_vs_regime_rule_spy_cash  spy_mcts_max_drawdown_delta_vs_regime_rule_spy_cash  spy_mcts_turnover_delta_vs_regime_rule_spy_cash
 exp_reward_simple     WEAK PASS      2.323296 0.076031 0.718259     -0.314583            0.197199                                    -0.000094                                       0.089849                                            -0.031393                                         0.161554
      benchmark_v1     WEAK PASS      1.870984 0.066468 0.653679     -0.260756            0.202776                                    -0.009657                                       0.025269                                             0.022434                                         0.167131
exp_prior_band_025     WEAK PASS      1.870984 0.066468 0.653679     -0.260756            0.202776                                    -0.009657                                       0.025269                                             0.022434                                         0.167131
exp_prior_band_050     WEAK PASS      1.870984 0.066468 0.653679     -0.260756            0.202776                                    -0.009657                                       0.025269                                             0.022434                                         0.167131
   exp_reward_risk     WEAK PASS      1.870984 0.066468 0.653679     -0.260756            0.202776                                    -0.009657                                       0.025269                                             0.022434                                         0.167131
```

## Best MultiAsset MCTS Experiment

```text
         experiment multi_asset_mcts_gate  total_return     cagr   sharpe  max_drawdown  avg_daily_turnover  multi_asset_mcts_cagr_delta_vs_regime_rule_multiasset  multi_asset_mcts_sharpe_delta_vs_regime_rule_multiasset  multi_asset_mcts_max_drawdown_delta_vs_regime_rule_multiasset  multi_asset_mcts_turnover_delta_vs_regime_rule_multiasset
  exp_reward_simple                  FAIL      2.435649 0.078216 0.665815      -0.32034            0.759821                                              -0.059272                                                -0.226935                                                      -0.037149                                                   0.688288
       benchmark_v1                  FAIL      1.886112 0.066810 0.583724      -0.30300            0.757274                                              -0.070678                                                -0.309026                                                      -0.019810                                                   0.685742
 exp_prior_band_025                  FAIL      1.886112 0.066810 0.583724      -0.30300            0.757274                                              -0.070678                                                -0.309026                                                      -0.019810                                                   0.685742
 exp_prior_band_050                  FAIL      1.886112 0.066810 0.583724      -0.30300            0.757274                                              -0.070678                                                -0.309026                                                      -0.019810                                                   0.685742
exp_prior_full_grid                  FAIL      1.886112 0.066810 0.583724      -0.30300            0.757274                                              -0.070678                                                -0.309026                                                      -0.019810                                                   0.685742
```

## Best by SPY MCTS Calmar Delta

```text
        experiment spy_mcts_gate     cagr   sharpe   calmar  max_drawdown  spy_mcts_calmar_delta_vs_regime_rule_spy_cash
 exp_sampler_daily     WEAK PASS 0.065304 0.642349 0.301572     -0.216544                                       0.032759
      benchmark_v1     WEAK PASS 0.066468 0.653679 0.254905     -0.260756                                      -0.013908
exp_prior_band_025     WEAK PASS 0.066468 0.653679 0.254905     -0.260756                                      -0.013908
exp_prior_band_050     WEAK PASS 0.066468 0.653679 0.254905     -0.260756                                      -0.013908
   exp_reward_risk     WEAK PASS 0.066468 0.653679 0.254905     -0.260756                                      -0.013908
```

## Best by MultiAsset MCTS Calmar Delta

```text
         experiment multi_asset_mcts_gate     cagr   sharpe   calmar  max_drawdown  multi_asset_mcts_calmar_delta_vs_regime_rule_multiasset
  exp_reward_simple                  FAIL 0.078216 0.665815 0.244167      -0.32034                                                -0.241330
       benchmark_v1                  FAIL 0.066810 0.583724 0.220495      -0.30300                                                -0.265002
 exp_prior_band_025                  FAIL 0.066810 0.583724 0.220495      -0.30300                                                -0.265002
 exp_prior_band_050                  FAIL 0.066810 0.583724 0.220495      -0.30300                                                -0.265002
exp_prior_full_grid                  FAIL 0.066810 0.583724 0.220495      -0.30300                                                -0.265002
```

## Experiments to Promote

```text
None
```

## Experiments Needing Follow-up

```text
None
```

## Rejected Experiments

```text
         experiment decision hypothesis_supported          primary_failure_mode                                                               next_recommended_experiment
exp_prior_full_grid   REJECT                False multi_asset_turnover_too_high Test MultiAsset template persistence or turnover damping in a single-variable experiment.
```

## Recommended Next Experiments

- Promote or retest the strongest SPY-only candidate: exp_reward_simple (WEAK PASS).
- Use multi-asset results as diagnostics until a candidate improves versus Regime Rule: current best is exp_reward_simple (FAIL).
- Investigate FAIL experiments before expanding the matrix.
- Keep walk-forward validation out of this benchmark until full-sample experiments stabilize.

## Required Artifacts

Each experiment directory contains `config_snapshot.yaml`, `metrics.csv`, `equity_curve.csv`, `drawdown.csv`, `strategy_diagnostics.csv`, `mcts_root_values.csv`, and `review.json`.
