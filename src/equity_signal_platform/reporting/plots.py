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


def plot_rolling_metrics(rolling_metrics: pd.DataFrame, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    columns = [column for column in rolling_metrics.columns if column in rolling_metrics]
    fig, axes = plt.subplots(len(columns), 1, figsize=(10, max(3, 2.4 * len(columns))), sharex=True)
    if len(columns) == 1:
        axes = [axes]
    for ax, column in zip(axes, columns):
        rolling_metrics[column].plot(ax=ax, linewidth=1.6)
        ax.set_title(column.replace("_", " ").title())
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_regime_performance(regime_summary: pd.DataFrame, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if regime_summary.empty:
        return

    fig, ax = plt.subplots(figsize=(9, 4.5))
    regime_summary["annualized_return"].plot(kind="bar", ax=ax, color="#4c78a8")
    ax.set_title("Annualized Return By Regime")
    ax.set_ylabel("Annualized Return")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_factor_diagnostics(factor_summary: pd.DataFrame, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if factor_summary.empty:
        return

    metrics = ["mean_ic", "hit_rate", "average_dispersion"]
    fig, axes = plt.subplots(1, len(metrics), figsize=(12, 4))
    for ax, metric in zip(axes, metrics):
        factor_summary[metric].plot(kind="bar", ax=ax)
        ax.set_title(metric.replace("_", " ").title())
        ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
