from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.config import DATA_DIR, ROOT, load_config
from src.main import run_pipeline


CONFIGS_DIR = ROOT / "configs"
EXPERIMENTS_DIR = ROOT / "experiments"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a matrix of Market Attractor MCTS experiments.")
    parser.add_argument("--base-config", default=str(ROOT / "config.yaml"), help="Base config path")
    parser.add_argument("--configs-dir", default=str(CONFIGS_DIR), help="Directory of experiment YAML files")
    parser.add_argument("--experiments-dir", default=str(EXPERIMENTS_DIR), help="Output directory")
    parser.add_argument("--force-download", action="store_true", help="Re-download yfinance data")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_config = load_config(args.base_config)
    configs_dir = Path(args.configs_dir)
    experiments_dir = Path(args.experiments_dir)
    experiments_dir.mkdir(parents=True, exist_ok=True)

    all_rows = []
    experiment_summaries = []
    config_paths = sorted(configs_dir.glob("*.yaml"))
    if not config_paths:
        raise RuntimeError(f"No experiment configs found under {configs_dir}")

    for config_path in config_paths:
        experiment_config = _load_yaml(config_path)
        config = _deep_merge(copy.deepcopy(base_config), experiment_config)
        experiment_name = config.get("experiment", {}).get("name") or config_path.stem
        experiment_dir = experiments_dir / experiment_name
        experiment_dir.mkdir(parents=True, exist_ok=True)

        with (experiment_dir / "config_snapshot.yaml").open("w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, sort_keys=False)

        print(f"Running {experiment_name}...")
        result = run_pipeline(
            config,
            data_dir=DATA_DIR,
            output_dir=experiment_dir,
            reports_dir=experiment_dir,
            plots_dir=experiment_dir / "plots",
            force_download=args.force_download,
        )

        metrics = result["metrics"].copy()
        comparisons = _build_comparisons(metrics)
        gate = _acceptance_gate(comparisons)
        metrics.insert(0, "experiment", experiment_name)
        metrics["acceptance_gate"] = gate
        for key, value in comparisons.items():
            metrics[key] = value
        all_rows.append(metrics)
        experiment_summaries.append({"experiment": experiment_name, "acceptance_gate": gate, **comparisons})

        args.force_download = False

    results_summary = pd.concat(all_rows, ignore_index=True)
    results_summary.to_csv(experiments_dir / "results_summary.csv", index=False)
    pd.DataFrame(experiment_summaries).to_csv(experiments_dir / "comparison_summary.csv", index=False)
    _write_report(experiments_dir / "report.md", results_summary, pd.DataFrame(experiment_summaries))
    print(f"Wrote experiment summary to {experiments_dir}")


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def _metric_row(metrics: pd.DataFrame, strategy: str) -> pd.Series:
    rows = metrics.loc[metrics["strategy"] == strategy]
    if rows.empty:
        raise KeyError(f"Missing strategy in metrics: {strategy}")
    return rows.iloc[0]


def _build_comparisons(metrics: pd.DataFrame) -> dict[str, float]:
    mcts = _metric_row(metrics, "Market Attractor MCTS")
    buy_hold = _metric_row(metrics, "Buy & Hold")
    spy_cash = _metric_row(metrics, "Regime Rule SPY/Cash")
    regime_rule_multi = _metric_row(metrics, "Regime Rule")

    comparisons: dict[str, float] = {}
    for label, benchmark in (
        ("buy_hold", buy_hold),
        ("regime_rule_spy_cash", spy_cash),
        ("regime_rule_multiasset", regime_rule_multi),
    ):
        comparisons[f"mcts_cagr_delta_vs_{label}"] = float(mcts["cagr"] - benchmark["cagr"])
        comparisons[f"mcts_sharpe_delta_vs_{label}"] = float(mcts["sharpe"] - benchmark["sharpe"])
        comparisons[f"mcts_max_drawdown_delta_vs_{label}"] = float(
            mcts["max_drawdown"] - benchmark["max_drawdown"]
        )
        comparisons[f"mcts_turnover_delta_vs_{label}"] = float(
            mcts["avg_daily_turnover"] - benchmark["avg_daily_turnover"]
        )
    return comparisons


def _acceptance_gate(comparisons: dict[str, float]) -> str:
    cagr = comparisons["mcts_cagr_delta_vs_regime_rule_spy_cash"]
    sharpe = comparisons["mcts_sharpe_delta_vs_regime_rule_spy_cash"]
    max_dd = comparisons["mcts_max_drawdown_delta_vs_regime_rule_spy_cash"]
    turnover = comparisons["mcts_turnover_delta_vs_regime_rule_spy_cash"]

    if cagr >= 0 and sharpe >= 0 and max_dd >= 0 and turnover <= 0:
        return "PASS"
    if cagr >= -0.02 and sharpe >= -0.05 and max_dd >= -0.05:
        return "WEAK PASS"
    return "FAIL"


def _write_report(path: Path, results_summary: pd.DataFrame, comparison_summary: pd.DataFrame) -> None:
    mcts_rows = results_summary.loc[results_summary["strategy"] == "Market Attractor MCTS"].copy()
    mcts_rows = mcts_rows.sort_values(
        ["acceptance_gate", "mcts_sharpe_delta_vs_regime_rule_spy_cash", "cagr"],
        ascending=[True, False, False],
    )

    gate_counts = comparison_summary["acceptance_gate"].value_counts().to_frame("count")
    lines = [
        "# Experiment Matrix Report",
        "",
        "This is a full-sample exploratory benchmark. It is intentionally not walk-forward yet.",
        "",
        "## Acceptance Gate",
        "",
        "- `PASS`: MCTS beats Regime Rule SPY/Cash on CAGR, Sharpe, max drawdown, and turnover.",
        "- `WEAK PASS`: MCTS is close to Regime Rule SPY/Cash on CAGR/Sharpe/drawdown.",
        "- `FAIL`: MCTS is not close enough to the SPY-only regime benchmark.",
        "",
        "## Gate Counts",
        "",
        "```text",
        gate_counts.to_string(),
        "```",
        "",
        "## Experiment Comparison Summary",
        "",
        "```text",
        comparison_summary.to_string(index=False),
        "```",
        "",
        "## MCTS Strategy Rows",
        "",
        "```text",
        mcts_rows[
            [
                "experiment",
                "acceptance_gate",
                "total_return",
                "cagr",
                "sharpe",
                "max_drawdown",
                "avg_daily_turnover",
                "mcts_cagr_delta_vs_regime_rule_spy_cash",
                "mcts_sharpe_delta_vs_regime_rule_spy_cash",
                "mcts_max_drawdown_delta_vs_regime_rule_spy_cash",
                "mcts_turnover_delta_vs_regime_rule_spy_cash",
            ]
        ].to_string(index=False),
        "```",
        "",
        "## Required Artifacts",
        "",
        "Each experiment directory contains `config_snapshot.yaml`, `metrics.csv`, `equity_curve.csv`, "
        "`drawdown.csv`, `strategy_diagnostics.csv`, and `mcts_root_values.csv`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
