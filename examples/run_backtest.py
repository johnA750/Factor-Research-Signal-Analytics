from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from equity_signal_platform.analytics import performance_summary
from equity_signal_platform.backtesting import run_backtest
from equity_signal_platform.config import PlatformConfig
from equity_signal_platform.data import download_adjusted_prices
from equity_signal_platform.reporting import plot_drawdown, plot_equity_curve
from equity_signal_platform.signals import compute_factor_scores
from equity_signal_platform.universe import get_universe


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an equity factor backtest.")
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config file.")
    args = parser.parse_args()

    config = PlatformConfig.from_yaml(args.config)
    data_config = config.section("data")
    universe_config = config.section("universe")
    signal_config = config.section("signals")
    portfolio_config = config.section("portfolio")
    backtest_config = config.section("backtest")
    reporting_config = config.section("reporting")

    output_dir = Path(reporting_config.get("output_dir", "reports"))
    output_dir.mkdir(parents=True, exist_ok=True)

    tickers = get_universe(universe_config)
    prices = download_adjusted_prices(
        tickers=tickers,
        start=data_config.get("start_date", "2018-01-01"),
        end=data_config.get("end_date"),
        auto_adjust=data_config.get("auto_adjust", True),
        cache_path=output_dir / "prices.csv",
    )

    factors = compute_factor_scores(prices, signal_config)
    result = run_backtest(
        prices=prices,
        scores=factors["composite"],
        volatility=factors["volatility"],
        top_n=portfolio_config.get("top_n", 8),
        weighting=portfolio_config.get("weighting", "inverse_volatility"),
        rebalance_frequency=backtest_config.get("rebalance_frequency", "ME"),
        transaction_cost_bps=backtest_config.get("transaction_cost_bps", 10),
        slippage_bps=backtest_config.get("slippage_bps", 5),
        initial_capital=backtest_config.get("initial_capital", 100_000),
    )

    summary = performance_summary(
        returns=result.returns,
        equity_curve=result.equity_curve,
        turnover=result.turnover,
        risk_free_rate=backtest_config.get("risk_free_rate", 0.0),
    )

    results = pd.DataFrame(
        {
            "strategy_return": result.returns,
            "equity_curve": result.equity_curve,
            "turnover": result.turnover,
            "costs": result.costs,
        }
    )
    results.to_csv(output_dir / "backtest_results.csv")
    summary.to_frame("value").to_csv(output_dir / "performance_summary.csv")

    latest_scores = factors["composite"].dropna(how="all").iloc[-1].sort_values(ascending=False)
    latest_scores.to_frame("composite_score").to_csv(output_dir / "latest_signal_ranks.csv")

    plot_equity_curve(result.equity_curve, output_dir / "equity_curve.png")
    plot_drawdown(result.equity_curve, output_dir / "drawdown.png")

    print("Backtest complete.")
    print(summary.to_string(float_format=lambda value: f"{value:0.4f}"))
    print(f"Reports written to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()

