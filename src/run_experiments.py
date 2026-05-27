from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
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
        metadata = _experiment_metadata(config, experiment_name)
        comparisons = _build_comparisons(metrics)
        gates = _build_gates(comparisons)
        contract_review = _strategy_contract_review(result["prices"], result["strategy_weights"])
        leakage_review = _leakage_review()
        review = _build_review(
            metadata,
            gates,
            comparisons,
            leakage_review,
            contract_review,
        )
        with (experiment_dir / "review.json").open("w", encoding="utf-8") as f:
            json.dump(review, f, indent=2)

        metrics.insert(0, "experiment", experiment_name)
        for key, value in metadata.items():
            metrics[key] = value
        for key, value in gates.items():
            metrics[key] = value
        for key in (
            "hypothesis_supported",
            "decision",
            "primary_failure_mode",
            "next_recommended_experiment",
            "leakage_level",
        ):
            metrics[key] = review[key]
        for key, value in comparisons.items():
            metrics[key] = value
        all_rows.append(metrics)
        experiment_summaries.append(
            {
                **metadata,
                **gates,
                "hypothesis_supported": review["hypothesis_supported"],
                "decision": review["decision"],
                "primary_failure_mode": review["primary_failure_mode"],
                "next_recommended_experiment": review["next_recommended_experiment"],
                "leakage_level": review["leakage_level"],
                "contract_review_passed": contract_review["passed"],
                **comparisons,
            }
        )

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


def _experiment_metadata(config: dict[str, Any], experiment_name: str) -> dict[str, str]:
    experiment = config.get("experiment", {})
    return {
        "experiment": experiment_name,
        "hypothesis": str(experiment.get("hypothesis", "")),
        "changed_variable": str(experiment.get("changed_variable", "")),
        "baseline_experiment": str(experiment.get("baseline_experiment", "")),
        "expected_result": str(experiment.get("expected_result", "")),
        "success_criteria": str(experiment.get("success_criteria", "")),
    }


def _build_comparisons(metrics: pd.DataFrame) -> dict[str, float]:
    spy_mcts = _metric_row(metrics, "Market Attractor MCTS")
    multi_mcts = _metric_row(metrics, "Market Attractor MCTS MultiAsset")
    buy_hold = _metric_row(metrics, "Buy & Hold")
    spy_cash = _metric_row(metrics, "Regime Rule SPY/Cash")
    regime_rule_multi = _metric_row(metrics, "Regime Rule")

    comparisons: dict[str, float] = {}
    for prefix, strategy_row, benchmarks in (
        (
            "spy_mcts",
            spy_mcts,
            (
                ("buy_hold", buy_hold),
                ("regime_rule_spy_cash", spy_cash),
                ("regime_rule_multiasset", regime_rule_multi),
            ),
        ),
        (
            "multi_asset_mcts",
            multi_mcts,
            (
                ("buy_hold", buy_hold),
                ("regime_rule_spy_cash", spy_cash),
                ("regime_rule_multiasset", regime_rule_multi),
            ),
        ),
    ):
        for label, benchmark in benchmarks:
            comparisons.update(_delta_metrics(prefix, label, strategy_row, benchmark))

    return comparisons


def _delta_metrics(prefix: str, label: str, strategy: pd.Series, benchmark: pd.Series) -> dict[str, float]:
    return {
        f"{prefix}_cagr_delta_vs_{label}": float(strategy["cagr"] - benchmark["cagr"]),
        f"{prefix}_sharpe_delta_vs_{label}": float(strategy["sharpe"] - benchmark["sharpe"]),
        f"{prefix}_calmar_delta_vs_{label}": float(strategy["calmar"] - benchmark["calmar"]),
        f"{prefix}_max_drawdown_delta_vs_{label}": float(
            strategy["max_drawdown"] - benchmark["max_drawdown"]
        ),
        f"{prefix}_turnover_delta_vs_{label}": float(
            strategy["avg_daily_turnover"] - benchmark["avg_daily_turnover"]
        ),
    }


def _build_gates(comparisons: dict[str, float]) -> dict[str, str]:
    spy_gate = _acceptance_gate(comparisons, "spy_mcts", "regime_rule_spy_cash")
    multi_gate = _acceptance_gate(comparisons, "multi_asset_mcts", "regime_rule_multiasset")
    return {
        "spy_mcts_gate": spy_gate,
        "multi_asset_mcts_gate": multi_gate,
        "overall_gate": _overall_gate(spy_gate, multi_gate),
    }


def _acceptance_gate(comparisons: dict[str, float], prefix: str, benchmark: str) -> str:
    cagr = comparisons[f"{prefix}_cagr_delta_vs_{benchmark}"]
    sharpe = comparisons[f"{prefix}_sharpe_delta_vs_{benchmark}"]
    max_dd = comparisons[f"{prefix}_max_drawdown_delta_vs_{benchmark}"]
    turnover = comparisons[f"{prefix}_turnover_delta_vs_{benchmark}"]

    if cagr >= 0 and sharpe >= 0 and max_dd >= 0 and turnover <= 0:
        return "PASS"
    if cagr >= -0.02 and sharpe >= -0.05 and max_dd >= -0.05:
        return "WEAK PASS"
    return "FAIL"


def _overall_gate(spy_gate: str, multi_gate: str) -> str:
    if spy_gate == "PASS" and multi_gate == "PASS":
        return "PASS"
    if spy_gate in {"PASS", "WEAK PASS"} and multi_gate in {"PASS", "WEAK PASS"}:
        return "WEAK PASS"
    return "FAIL"


def _leakage_review() -> dict[str, Any]:
    return {
        "leakage_level": "exploratory_full_sample",
        "known_lookahead_sources": [
            "full-sample regime fit",
            "full-sample future-return regime ranking",
            "full-sample MCTS path sampling",
        ],
        "blocks_run": False,
    }


def _strategy_contract_review(
    prices: pd.DataFrame,
    strategy_weights: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    strategy_results = {}
    overall_pass = True
    for strategy, weights in strategy_weights.items():
        aligned_index = weights.index.equals(prices.index)
        has_nan = bool(weights.isna().any().any())
        gross_exposure = weights.abs().sum(axis=1)
        max_abs_weight_sum = float(gross_exposure.max())
        leverage_ok = bool((gross_exposure <= 1.0001).all())
        abnormal_leverage = bool(max_abs_weight_sum > 1.0001)
        turnover = weights.diff().abs().sum(axis=1)
        turnover_calculable = bool(np.isfinite(turnover.fillna(0.0).to_numpy()).all())
        passed = aligned_index and not has_nan and leverage_ok and turnover_calculable and not abnormal_leverage
        overall_pass = overall_pass and passed
        strategy_results[strategy] = {
            "passed": passed,
            "has_nan": has_nan,
            "index_aligned_with_prices": bool(aligned_index),
            "max_abs_weight_sum": max_abs_weight_sum,
            "weight_abs_sum_lte_1_0001": leverage_ok,
            "turnover_calculable": turnover_calculable,
            "abnormal_leverage": abnormal_leverage,
        }
    return {"passed": overall_pass, "strategies": strategy_results}


def _build_review(
    metadata: dict[str, str],
    gates: dict[str, str],
    comparisons: dict[str, float],
    leakage_review: dict[str, Any],
    contract_review: dict[str, Any],
) -> dict[str, Any]:
    best_worst = _best_worst_metric_deltas(comparisons)
    hypothesis_supported = _hypothesis_supported(gates, comparisons, metadata)
    decision = _decision(gates, comparisons, contract_review)
    primary_failure_mode = _primary_failure_mode(gates, comparisons, contract_review)
    next_recommended_experiment = _next_recommended_experiment_for_review(
        decision,
        primary_failure_mode,
        metadata,
    )
    return {
        "experiment": metadata["experiment"],
        "hypothesis": metadata["hypothesis"],
        "changed_variable": metadata["changed_variable"],
        "baseline_experiment": metadata["baseline_experiment"],
        "expected_result": metadata["expected_result"],
        "success_criteria": metadata["success_criteria"],
        "hypothesis_supported": hypothesis_supported,
        "decision": decision,
        "primary_failure_mode": primary_failure_mode,
        "next_recommended_experiment": next_recommended_experiment,
        "gate_results": gates,
        **best_worst,
        "leakage_level": leakage_review["leakage_level"],
        "leakage_review": leakage_review,
        "strategy_contract_review": contract_review,
        "recommendation": _recommendation(gates, contract_review),
    }


def _hypothesis_supported(
    gates: dict[str, str],
    comparisons: dict[str, float],
    metadata: dict[str, str],
) -> bool | str:
    changed_variable = metadata["changed_variable"]
    if changed_variable == "none":
        return "inconclusive"
    spy_close = gates["spy_mcts_gate"] in {"PASS", "WEAK PASS"}
    multi_close = gates["multi_asset_mcts_gate"] in {"PASS", "WEAK PASS"}
    if spy_close and comparisons["spy_mcts_sharpe_delta_vs_regime_rule_spy_cash"] >= 0:
        return True
    if multi_close and comparisons["multi_asset_mcts_sharpe_delta_vs_regime_rule_multiasset"] >= 0:
        return True
    if gates["spy_mcts_gate"] == "FAIL" and gates["multi_asset_mcts_gate"] == "FAIL":
        return False
    return "inconclusive"


def _decision(
    gates: dict[str, str],
    comparisons: dict[str, float],
    contract_review: dict[str, Any],
) -> str:
    if not contract_review["passed"]:
        return "REJECT"
    if gates["spy_mcts_gate"] == "PASS" or gates["multi_asset_mcts_gate"] == "PASS":
        return "PROMOTE"
    spy_mixed = (
        gates["spy_mcts_gate"] == "WEAK PASS"
        and comparisons["spy_mcts_sharpe_delta_vs_regime_rule_spy_cash"] > 0
        and comparisons["spy_mcts_calmar_delta_vs_regime_rule_spy_cash"] > -0.05
    )
    multi_mixed = (
        gates["multi_asset_mcts_gate"] == "WEAK PASS"
        and comparisons["multi_asset_mcts_sharpe_delta_vs_regime_rule_multiasset"] > 0
        and comparisons["multi_asset_mcts_calmar_delta_vs_regime_rule_multiasset"] > -0.05
    )
    if spy_mixed or multi_mixed:
        return "KEEP_EXPLORATORY"
    if gates["spy_mcts_gate"] == "WEAK PASS" or gates["multi_asset_mcts_gate"] == "WEAK PASS":
        return "NEEDS_FOLLOWUP"
    return "REJECT"


def _primary_failure_mode(
    gates: dict[str, str],
    comparisons: dict[str, float],
    contract_review: dict[str, Any],
) -> str:
    if not contract_review["passed"]:
        return "strategy_contract_violation"
    if gates["multi_asset_mcts_gate"] == "FAIL" and comparisons["multi_asset_mcts_turnover_delta_vs_regime_rule_multiasset"] > 0.25:
        return "multi_asset_turnover_too_high"
    if gates["spy_mcts_gate"] == "FAIL" and comparisons["spy_mcts_turnover_delta_vs_regime_rule_spy_cash"] > 0.10:
        return "spy_mcts_turnover_too_high"
    if comparisons["spy_mcts_max_drawdown_delta_vs_regime_rule_spy_cash"] < -0.05:
        return "spy_mcts_drawdown_worse"
    if comparisons["spy_mcts_sharpe_delta_vs_regime_rule_spy_cash"] < 0:
        return "spy_mcts_sharpe_worse"
    if comparisons["multi_asset_mcts_sharpe_delta_vs_regime_rule_multiasset"] < 0:
        return "multi_asset_sharpe_worse"
    return "none_or_mixed"


def _next_recommended_experiment_for_review(
    decision: str,
    primary_failure_mode: str,
    metadata: dict[str, str],
) -> str:
    if decision == "PROMOTE":
        return "Promote this config as a benchmark candidate and retest robustness."
    if primary_failure_mode == "multi_asset_turnover_too_high":
        return "Test MultiAsset template persistence or turnover damping in a single-variable experiment."
    if primary_failure_mode == "spy_mcts_turnover_too_high":
        return "Test action_inertia_threshold variants in a single-variable experiment."
    if primary_failure_mode == "spy_mcts_drawdown_worse":
        return "Test lower-risk reward settings or drawdown penalty variants."
    if primary_failure_mode == "spy_mcts_sharpe_worse":
        return "Compare sampler or horizon variants before changing portfolio logic."
    if decision == "REJECT":
        return "Do not extend this branch; return to benchmark_v1 or the best WEAK PASS experiment."
    return f"Follow up on {metadata['changed_variable']} with a narrower single-variable experiment."


def _recommendation(gates: dict[str, str], contract_review: dict[str, Any]) -> str:
    if not contract_review["passed"]:
        return "Fix strategy contract violations before interpreting performance."
    if gates["overall_gate"] == "PASS":
        return "Promote this configuration to the next benchmark candidate."
    if gates["spy_mcts_gate"] in {"PASS", "WEAK PASS"} and gates["multi_asset_mcts_gate"] == "FAIL":
        return "Keep SPY-only setting for comparison; improve or constrain multi-asset MCTS before relying on it."
    if gates["spy_mcts_gate"] == "FAIL":
        return "Do not promote; investigate SPY-only MCTS underperformance versus SPY/Cash benchmark."
    return "Retain as exploratory comparison, not as a benchmark default."


def _best_worst_metric_deltas(comparisons: dict[str, float]) -> dict[str, dict[str, float | str]]:
    deltas = {key: value for key, value in comparisons.items() if "_delta_vs_" in key}
    best_key = max(deltas, key=deltas.get)
    worst_key = min(deltas, key=deltas.get)
    return {
        "best_metric_delta": {"metric": best_key, "value": deltas[best_key]},
        "worst_metric_delta": {"metric": worst_key, "value": deltas[worst_key]},
    }


def _write_report(path: Path, results_summary: pd.DataFrame, comparison_summary: pd.DataFrame) -> None:
    spy_rows = results_summary.loc[results_summary["strategy"] == "Market Attractor MCTS"].copy()
    multi_rows = results_summary.loc[results_summary["strategy"] == "Market Attractor MCTS MultiAsset"].copy()
    gate_counts = comparison_summary["overall_gate"].value_counts().to_frame("count")
    best_by_sharpe = results_summary.sort_values("sharpe", ascending=False).head(10)
    best_by_calmar = results_summary.sort_values("calmar", ascending=False).head(10)
    best_by_max_drawdown = results_summary.sort_values("max_drawdown", ascending=False).head(10)
    lowest_turnover = results_summary.sort_values("avg_daily_turnover").head(10)
    best_spy = _sort_by_gate(
        spy_rows,
        "spy_mcts_gate",
        "spy_mcts_sharpe_delta_vs_regime_rule_spy_cash",
    ).head(5)
    best_multi = _sort_by_gate(
        multi_rows,
        "multi_asset_mcts_gate",
        "multi_asset_mcts_sharpe_delta_vs_regime_rule_multiasset",
    ).head(5)
    best_spy_calmar = spy_rows.sort_values(
        "spy_mcts_calmar_delta_vs_regime_rule_spy_cash",
        ascending=False,
    ).head(5)
    best_multi_calmar = multi_rows.sort_values(
        "multi_asset_mcts_calmar_delta_vs_regime_rule_multiasset",
        ascending=False,
    ).head(5)
    promote = comparison_summary.loc[comparison_summary["decision"] == "PROMOTE"]
    followup = comparison_summary.loc[comparison_summary["decision"] == "NEEDS_FOLLOWUP"]
    rejected = comparison_summary.loc[comparison_summary["decision"] == "REJECT"]
    next_experiments = _next_recommended_experiments(comparison_summary)
    leakage = _leakage_review()
    lines = [
        "# Experiment Matrix Report",
        "",
        "This is a full-sample exploratory benchmark. It is intentionally not walk-forward yet.",
        "",
        "## Leakage Review",
        "",
        f"- Leakage level: `{leakage['leakage_level']}`",
        "- Known look-ahead sources:",
        *[f"  - {source}" for source in leakage["known_lookahead_sources"]],
        "- This does not block the current exploratory benchmark run.",
        "",
        "## Acceptance Gate",
        "",
        "- `spy_mcts_gate`: SPY-only MCTS versus Regime Rule SPY/Cash.",
        "- `multi_asset_mcts_gate`: MultiAsset MCTS versus Regime Rule.",
        "- `overall_gate`: combined result across both MCTS variants.",
        "- `PASS`: beats the relevant benchmark on CAGR, Sharpe, max drawdown, and turnover.",
        "- `WEAK PASS`: close to the relevant benchmark on CAGR, Sharpe, and drawdown.",
        "- `FAIL`: not close enough to the relevant benchmark.",
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
        "## Best by Sharpe",
        "",
        "```text",
        _leaderboard(best_by_sharpe),
        "```",
        "",
        "## Best by Calmar",
        "",
        "```text",
        _leaderboard(best_by_calmar),
        "```",
        "",
        "## Best by Max Drawdown",
        "",
        "```text",
        _leaderboard(best_by_max_drawdown),
        "```",
        "",
        "## Lowest Turnover",
        "",
        "```text",
        _leaderboard(lowest_turnover),
        "```",
        "",
        "## Best SPY-only MCTS Experiment",
        "",
        "```text",
        best_spy[
            [
                "experiment",
                "spy_mcts_gate",
                "total_return",
                "cagr",
                "sharpe",
                "max_drawdown",
                "avg_daily_turnover",
                "spy_mcts_cagr_delta_vs_regime_rule_spy_cash",
                "spy_mcts_sharpe_delta_vs_regime_rule_spy_cash",
                "spy_mcts_max_drawdown_delta_vs_regime_rule_spy_cash",
                "spy_mcts_turnover_delta_vs_regime_rule_spy_cash",
            ]
        ].to_string(index=False),
        "```",
        "",
        "## Best MultiAsset MCTS Experiment",
        "",
        "```text",
        best_multi[
            [
                "experiment",
                "multi_asset_mcts_gate",
                "total_return",
                "cagr",
                "sharpe",
                "max_drawdown",
                "avg_daily_turnover",
                "multi_asset_mcts_cagr_delta_vs_regime_rule_multiasset",
                "multi_asset_mcts_sharpe_delta_vs_regime_rule_multiasset",
                "multi_asset_mcts_max_drawdown_delta_vs_regime_rule_multiasset",
                "multi_asset_mcts_turnover_delta_vs_regime_rule_multiasset",
            ]
        ].to_string(index=False),
        "```",
        "",
        "## Best by SPY MCTS Calmar Delta",
        "",
        "```text",
        best_spy_calmar[
            [
                "experiment",
                "spy_mcts_gate",
                "cagr",
                "sharpe",
                "calmar",
                "max_drawdown",
                "spy_mcts_calmar_delta_vs_regime_rule_spy_cash",
            ]
        ].to_string(index=False),
        "```",
        "",
        "## Best by MultiAsset MCTS Calmar Delta",
        "",
        "```text",
        best_multi_calmar[
            [
                "experiment",
                "multi_asset_mcts_gate",
                "cagr",
                "sharpe",
                "calmar",
                "max_drawdown",
                "multi_asset_mcts_calmar_delta_vs_regime_rule_multiasset",
            ]
        ].to_string(index=False),
        "```",
        "",
        "## Experiments to Promote",
        "",
        "```text",
        _decision_table(promote),
        "```",
        "",
        "## Experiments Needing Follow-up",
        "",
        "```text",
        _decision_table(followup),
        "```",
        "",
        "## Rejected Experiments",
        "",
        "```text",
        _decision_table(rejected),
        "```",
        "",
        "## Recommended Next Experiments",
        "",
        *[f"- {item}" for item in next_experiments],
        "",
        "## Required Artifacts",
        "",
        "Each experiment directory contains `config_snapshot.yaml`, `metrics.csv`, `equity_curve.csv`, "
        "`drawdown.csv`, `strategy_diagnostics.csv`, `mcts_root_values.csv`, and `review.json`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _leaderboard(rows: pd.DataFrame) -> str:
    return rows[
        [
            "experiment",
            "strategy",
            "overall_gate",
            "total_return",
            "cagr",
            "sharpe",
            "calmar",
            "max_drawdown",
            "avg_daily_turnover",
        ]
    ].to_string(index=False)


def _sort_by_gate(rows: pd.DataFrame, gate_col: str, score_col: str) -> pd.DataFrame:
    gate_rank = {"PASS": 0, "WEAK PASS": 1, "FAIL": 2}
    sortable = rows.copy()
    sortable["_gate_rank"] = sortable[gate_col].map(gate_rank).fillna(99)
    return sortable.sort_values(["_gate_rank", score_col, "cagr"], ascending=[True, False, False])


def _decision_table(rows: pd.DataFrame) -> str:
    if rows.empty:
        return "None"
    return rows[
        [
            "experiment",
            "decision",
            "hypothesis_supported",
            "primary_failure_mode",
            "next_recommended_experiment",
        ]
    ].to_string(index=False)


def _next_recommended_experiments(comparison_summary: pd.DataFrame) -> list[str]:
    recommendations = []
    best_spy = comparison_summary.sort_values(
        "spy_mcts_sharpe_delta_vs_regime_rule_spy_cash",
        ascending=False,
    ).iloc[0]
    recommendations.append(
        "Promote or retest the strongest SPY-only candidate: "
        f"{best_spy['experiment']} ({best_spy['spy_mcts_gate']})."
    )
    best_multi = comparison_summary.sort_values(
        "multi_asset_mcts_sharpe_delta_vs_regime_rule_multiasset",
        ascending=False,
    ).iloc[0]
    recommendations.append(
        "Use multi-asset results as diagnostics until a candidate improves versus Regime Rule: "
        f"current best is {best_multi['experiment']} ({best_multi['multi_asset_mcts_gate']})."
    )
    if (comparison_summary["overall_gate"] == "FAIL").any():
        recommendations.append("Investigate FAIL experiments before expanding the matrix.")
    recommendations.append("Keep walk-forward validation out of this benchmark until full-sample experiments stabilize.")
    return recommendations


if __name__ == "__main__":
    main()
