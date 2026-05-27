# market-attractor-mcts

Python research project for testing a first-pass **Market Attractor Guided MCTS** strategy on US ETF daily data.

The pipeline downloads historical daily prices for:

- SPY
- QQQ
- IWM
- TLT
- GLD
- ^VIX

It builds market-state features, discovers market regimes with KMeans and `hmmlearn` Gaussian HMM, summarizes future regime behavior, runs baseline strategies, runs a simplified long-only SPY MCTS strategy, and writes research outputs.

## Important Caveat

This first version intentionally allows **exploratory full-sample regime discovery**. KMeans/HMM regimes are fit using the full dataset, and the regime rule also ranks regimes using full-sample future returns.

That means the reported strategy backtests are **not tradable, production-valid, or free of look-ahead bias**. Treat them as exploratory research diagnostics only.

A tradable next version should use walk-forward validation:

- fit scalers and regime models only on past data,
- infer the next period's regime out of sample,
- estimate regime statistics using only past observations,
- run MCTS with only information available at the decision date,
- compare stability across walk-forward folds.

## Project Structure

```text
market-attractor-mcts/
  config.yaml
  requirements.txt
  README.md
  src/
    backtest.py
    config.py
    data.py
    features.py
    main.py
    mcts.py
    plots.py
    regime.py
    strategies.py
```

Generated files are written to:

```text
data/
  prices.csv
outputs/
  features.csv
  regime_labels.csv
  regime_summary.csv
  metrics.csv
  equity_curve.csv
  drawdown.csv
  plots/
    equity_curves.png
    drawdowns.png
reports/
  diagnostics.md
  mcts_position.csv
  mcts_position.png
  mcts_regime_stats.csv
  strategy_diagnostics.csv
```

## Setup

```bash
cd market-attractor-mcts
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python3 -m src.main
```

Force a fresh yfinance download:

```bash
python3 -m src.main --force-download
```

## Run Experiment Matrix

The reproducible benchmark suite lives under `configs/`. Each YAML file is merged onto `config.yaml`, then the same pipeline used by `src.main` is run into a dedicated experiment directory.

```bash
python3 -m src.run_experiments
```

Experiment outputs are written to:

```text
experiments/
  results_summary.csv
  comparison_summary.csv
  report.md
  benchmark_v1/
    config_snapshot.yaml
    metrics.csv
    equity_curve.csv
    drawdown.csv
    strategy_diagnostics.csv
    mcts_root_values.csv
```

The report assigns an acceptance gate for each experiment:

- `PASS`: MCTS beats Regime Rule SPY/Cash on CAGR, Sharpe, max drawdown, and turnover.
- `WEAK PASS`: MCTS is close to Regime Rule SPY/Cash on CAGR, Sharpe, and drawdown.
- `FAIL`: MCTS is not close enough to the SPY-only regime benchmark.

This matrix is still full-sample exploratory research, not walk-forward validation.

## Features

The feature set includes:

- 1/5/20 day ETF returns,
- 20/60 day annualized volatility,
- 50/200 day moving-average deviation,
- 20/60 day relative strength versus SPY,
- VIX level,
- VIX 1/5 day change,
- VIX rolling z-score.

## Regime Discovery

The project fits:

- `sklearn.cluster.KMeans`
- `hmmlearn.hmm.GaussianHMM`

For each KMeans and HMM regime, `outputs/regime_summary.csv` reports future SPY behavior over 1/5/20 trading days:

- average forward return,
- median forward return,
- forward realized volatility,
- win rate,
- downside volatility,
- 5% CVaR.

## Strategies

Baseline strategies:

- **Buy & Hold**: 100% SPY.
- **MA200 Trend**: 100% SPY when SPY is above its 200-day moving average, otherwise cash.
- **Vol Target**: scales SPY exposure to a target annualized volatility, capped at 1.0x.
- **Regime Rule**: risk-on in favorable full-sample HMM regimes; otherwise rotates equally into configured safe assets.

MCTS strategy:

- trades only SPY,
- long-only,
- position grid `[0, 0.25, 0.5, 0.75, 1.0]`,
- search horizon `5`,
- daily simulations `100`,
- default sampler draws historical continuous return paths from dates in the same regime,
- reward starts from return minus transaction cost, then applies a configurable risk penalty and opportunity cost,
- Regime Rule SPY exposure is used as a prior, with default candidate actions near the prior.

The original single-day regime sampler is still available by setting `mcts.sampler: "regime_daily"`.

## Outputs

`outputs/metrics.csv` contains strategy-level performance statistics:

- total return,
- CAGR,
- annual volatility,
- Sharpe ratio,
- max drawdown,
- Calmar ratio,
- daily win rate,
- average daily turnover.

`outputs/equity_curve.csv` and `outputs/drawdown.csv` contain daily time series for all strategies. Matplotlib charts are saved under `outputs/plots/`.
