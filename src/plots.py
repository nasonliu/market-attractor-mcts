from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


def plot_equity_curves(equity_curves: pd.DataFrame, output_dir: Path) -> Path:
    path = output_dir / "equity_curves.png"
    fig, ax = plt.subplots(figsize=(12, 7))
    equity_curves.plot(ax=ax, linewidth=1.4)
    ax.set_title("Strategy Equity Curves")
    ax.set_xlabel("Date")
    ax.set_ylabel("Growth of $1")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_drawdowns(drawdowns: pd.DataFrame, output_dir: Path) -> Path:
    path = output_dir / "drawdowns.png"
    fig, ax = plt.subplots(figsize=(12, 7))
    drawdowns.plot(ax=ax, linewidth=1.2)
    ax.set_title("Strategy Drawdowns")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_mcts_position(position: pd.Series, output_dir: Path) -> Path:
    path = output_dir / "mcts_position.png"
    fig, ax = plt.subplots(figsize=(12, 4.5))
    position.plot(ax=ax, linewidth=1.0)
    ax.set_title("MCTS SPY Position")
    ax.set_xlabel("Date")
    ax.set_ylabel("Target Position")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path
