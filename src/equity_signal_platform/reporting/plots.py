from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_equity_curve(equity_curve: pd.Series, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    equity_curve.plot(ax=ax, color="#1f77b4", linewidth=2)
    ax.set_title("Strategy Equity Curve")
    ax.set_xlabel("")
    ax.set_ylabel("Portfolio Value")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_drawdown(equity_curve: pd.Series, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    drawdown = equity_curve / equity_curve.cummax() - 1.0
    fig, ax = plt.subplots(figsize=(10, 4))
    drawdown.plot(ax=ax, color="#d62728", linewidth=1.8)
    ax.fill_between(drawdown.index, drawdown.values, 0, color="#d62728", alpha=0.2)
    ax.set_title("Strategy Drawdown")
    ax.set_xlabel("")
    ax.set_ylabel("Drawdown")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

