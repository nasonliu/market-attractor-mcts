from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest import run_backtest, summarize_metrics
from src.config import DATA_DIR, OUTPUT_DIR, PLOTS_DIR, REPORTS_DIR, ensure_directories, load_config
from src.data import download_prices
from src.diagnostics import (
    mcts_regime_position_stats,
    root_edge_diagnostics,
    strategy_position_diagnostics,
    write_diagnostics_markdown,
)
from src.features import build_features
from src.mcts import build_mcts_weights, build_multi_asset_mcts_weights
from src.plots import plot_drawdowns, plot_equity_curves, plot_mcts_position
from src.regime import compute_regime_summary, identify_regimes
from src.strategies import buy_and_hold, ma200_trend, regime_rule, regime_rule_spy_cash, vol_target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Market Attractor Guided MCTS research pipeline.")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--force-download", action="store_true", help="Re-download yfinance data")
    return parser.parse_args()


def run_pipeline(
    config: dict[str, Any],
    data_dir: Path = DATA_DIR,
    output_dir: Path = OUTPUT_DIR,
    reports_dir: Path = REPORTS_DIR,
    plots_dir: Path | None = None,
    force_download: bool = False,
) -> dict[str, pd.DataFrame]:
    plots_dir = plots_dir or output_dir / "plots"
    for path in (data_dir, output_dir, reports_dir, plots_dir):
        path.mkdir(parents=True, exist_ok=True)

    prices = download_prices(config, data_dir, force=force_download)
    prices.to_csv(data_dir / "prices.csv")

    features = build_features(prices, config)
    features.to_csv(output_dir / "features.csv")

    regimes, _ = identify_regimes(features, config)
    regimes.to_csv(output_dir / "regime_labels.csv")

    trading_days = int(config["backtest"]["trading_days"])
    regime_summary = compute_regime_summary(prices, regimes, trading_days=trading_days)
    regime_summary.to_csv(output_dir / "regime_summary.csv", index=False)

    buy_hold_weights = buy_and_hold(prices)
    ma200_weights = ma200_trend(prices, window=int(config["backtest"]["ma_window"]))
    vol_target_weights = vol_target(
        prices,
        target_vol_annual=float(config["backtest"]["vol_target_annual"]),
        max_leverage=float(config["backtest"]["max_leverage"]),
    )
    regime_rule_weights = regime_rule(
        prices,
        regimes,
        safe_assets=list(config["backtest"]["regime_rule_safe_assets"]),
        method="hmm_regime",
    )
    regime_rule_spy_cash_weights = regime_rule_spy_cash(
        prices,
        regimes,
        method="hmm_regime",
    )
    mcts_weights = build_mcts_weights(
        prices,
        regimes,
        config,
        method="hmm_regime",
        prior_weights=regime_rule_weights,
        root_values_path=reports_dir / "mcts_root_values.csv",
    )
    multi_asset_mcts_weights = build_multi_asset_mcts_weights(
        prices,
        regimes,
        config,
        method="hmm_regime",
        template_path=reports_dir / "multi_asset_mcts_template.csv",
        root_values_path=reports_dir / "multi_asset_mcts_root_values.csv",
    )

    strategy_weights = {
        "Buy & Hold": buy_hold_weights,
        "MA200 Trend": ma200_weights,
        "Vol Target": vol_target_weights,
        "Regime Rule": regime_rule_weights,
        "Regime Rule SPY/Cash": regime_rule_spy_cash_weights,
        "Market Attractor MCTS": mcts_weights,
        "Market Attractor MCTS MultiAsset": multi_asset_mcts_weights,
    }

    metrics_rows = []
    equity_curves = pd.DataFrame(index=prices.index)
    drawdowns = pd.DataFrame(index=prices.index)

    for name, weights in strategy_weights.items():
        cost_bps = (
            float(config["mcts"]["transaction_cost_bps"])
            if name.startswith("Market Attractor MCTS")
            else float(config["backtest"]["transaction_cost_bps"])
        )
        result = run_backtest(
            prices,
            weights,
            transaction_cost_bps=cost_bps,
            initial_capital=float(config["backtest"]["initial_capital"]),
        )
        equity_curves[name] = result["equity"]
        drawdowns[name] = result["drawdown"]
        metrics_rows.append(
            summarize_metrics(
                strategy_name=name,
                returns=result["returns"],
                equity=result["equity"],
                drawdown=result["drawdown"],
                turnover=result["turnover"],
                trading_days=trading_days,
            )
        )

    metrics = pd.DataFrame(metrics_rows)
    metrics.to_csv(output_dir / "metrics.csv", index=False)
    equity_curves.to_csv(output_dir / "equity_curve.csv")
    drawdowns.to_csv(output_dir / "drawdown.csv")

    plot_equity_curves(equity_curves, plots_dir)
    plot_drawdowns(drawdowns, plots_dir)

    asset = str(config["mcts"]["asset"])
    mcts_position = pd.DataFrame(
        {
            "mcts_position": mcts_weights[asset].reindex(prices.index).ffill().fillna(0.0),
            "regime_rule_prior": regime_rule_weights[asset].reindex(prices.index).ffill().fillna(0.0),
        },
        index=prices.index,
    )
    mcts_position.to_csv(reports_dir / "mcts_position.csv")
    plot_mcts_position(mcts_position["mcts_position"], reports_dir)

    strategy_diagnostics = strategy_position_diagnostics(
        strategy_weights,
        asset=asset,
        trading_days=trading_days,
    )
    strategy_diagnostics.to_csv(reports_dir / "strategy_diagnostics.csv", index=False)
    pd.DataFrame(
        [{"parameter": key, "value": value} for key, value in config["mcts"].items()]
    ).to_csv(reports_dir / "mcts_config.csv", index=False)

    mcts_regime_stats = mcts_regime_position_stats(
        prices,
        regimes,
        mcts_weights,
        regime_rule_weights,
        asset=asset,
        method="hmm_regime",
    )
    mcts_regime_stats.to_csv(reports_dir / "mcts_regime_stats.csv", index=False)

    root_values = pd.read_csv(reports_dir / "mcts_root_values.csv")
    multi_asset_templates = pd.read_csv(reports_dir / "multi_asset_mcts_template.csv")
    multi_asset_root_values = pd.read_csv(reports_dir / "multi_asset_mcts_root_values.csv")
    spy_edge_diagnostics = root_edge_diagnostics(
        root_values,
        action_levels=[float(value) for value in config["mcts"]["positions"]],
        chosen_col="chosen_position",
        previous_col="previous_position",
        value_prefix="value_",
    )
    spy_edge_diagnostics.to_csv(reports_dir / "mcts_root_edge_diagnostics.csv", index=False)
    multi_asset_edge_diagnostics = root_edge_diagnostics(
        multi_asset_root_values,
        action_levels=[0, 1, 2, 3, 4],
        chosen_col="chosen_template",
        previous_col="previous_template",
        value_prefix="value_template_",
    )
    multi_asset_edge_diagnostics.to_csv(
        reports_dir / "multi_asset_mcts_root_edge_diagnostics.csv",
        index=False,
    )
    write_diagnostics_markdown(
        reports_dir / "diagnostics.md",
        metrics,
        strategy_diagnostics,
        mcts_regime_stats,
        config["mcts"],
        root_values,
        multi_asset_templates,
        multi_asset_root_values,
        spy_edge_diagnostics,
        multi_asset_edge_diagnostics,
    )

    return {
        "prices": prices,
        "metrics": metrics,
        "equity_curves": equity_curves,
        "drawdowns": drawdowns,
        "strategy_diagnostics": strategy_diagnostics,
        "mcts_root_values": root_values,
        "strategy_weights": strategy_weights,
    }


def main() -> None:
    args = parse_args()
    ensure_directories()
    config = load_config(args.config)
    result = run_pipeline(
        config,
        data_dir=DATA_DIR,
        output_dir=OUTPUT_DIR,
        reports_dir=REPORTS_DIR,
        plots_dir=PLOTS_DIR,
        force_download=args.force_download,
    )

    print(f"Wrote outputs to {OUTPUT_DIR}")
    print(f"Wrote reports to {REPORTS_DIR}")
    print(result["metrics"].to_string(index=False))


if __name__ == "__main__":
    main()
