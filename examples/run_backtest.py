from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from equity_signal_platform.analytics import (
    capm_regression,
    classify_market_regimes,
    factor_diagnostic_summary,
    performance_by_regime,
    performance_summary,
    rolling_metrics,
)
from equity_signal_platform.backtesting import run_backtest, run_walk_forward
from equity_signal_platform.config import PlatformConfig
from equity_signal_platform.data import download_adjusted_prices
from equity_signal_platform.reporting import (
    plot_drawdown,
    plot_equity_curve,
    plot_factor_diagnostics,
    plot_regime_performance,
    plot_rolling_metrics,
)
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
    regime_config = config.section("regime")
    rolling_config = config.section("rolling")
    factor_eval_config = config.section("factor_evaluation")
    walk_forward_config = config.section("walk_forward")

    output_dir = Path(reporting_config.get("output_dir", "reports"))
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmark_ticker = regime_config.get("benchmark_ticker", "SPY")
    tickers = sorted(set(get_universe(universe_config) + [benchmark_ticker]))
    prices = download_adjusted_prices(
        tickers=tickers,
        start=data_config.get("start_date", "2018-01-01"),
        end=data_config.get("end_date"),
        auto_adjust=data_config.get("auto_adjust", True),
        cache_path=output_dir / "prices.csv",
    )
    benchmark_prices = prices[benchmark_ticker] if benchmark_ticker in prices else None
    research_prices = prices.drop(columns=[benchmark_ticker], errors="ignore")

    factors = compute_factor_scores(research_prices, signal_config)
    result = run_backtest(
        prices=research_prices,
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

    rolling = rolling_metrics(
        result.returns,
        result.equity_curve,
        result.turnover,
        window=rolling_config.get("window_days", 126),
        risk_free_rate=backtest_config.get("risk_free_rate", 0.0),
    )
    rolling.to_csv(output_dir / "rolling_metrics.csv")

    factor_summary, factor_details = factor_diagnostic_summary(
        factors,
        research_prices,
        forward_return_days=factor_eval_config.get("forward_return_days", 21),
        decay_periods=factor_eval_config.get("decay_periods", [1, 5, 10, 21, 63]),
        persistence_lags=factor_eval_config.get("persistence_lags", [1, 5, 21, 63]),
    )
    factor_summary.to_csv(output_dir / "factor_summary.csv")
    for factor_name, details in factor_details.items():
        details.to_frame("value").to_csv(output_dir / f"factor_{factor_name}_details.csv")

    walk = run_walk_forward(
        prices=research_prices,
        factors=factors,
        volatility=factors["volatility"],
        train_months=walk_forward_config.get("train_months", 36),
        test_months=walk_forward_config.get("test_months", 12),
        min_train_observations=walk_forward_config.get("min_train_observations", 252),
        top_n=portfolio_config.get("top_n", 8),
        weighting=portfolio_config.get("weighting", "inverse_volatility"),
        rebalance_frequency=backtest_config.get("rebalance_frequency", "ME"),
        transaction_cost_bps=backtest_config.get("transaction_cost_bps", 10),
        slippage_bps=backtest_config.get("slippage_bps", 5),
        initial_capital=backtest_config.get("initial_capital", 100_000),
    )
    walk.returns.to_csv(output_dir / "walk_forward_returns.csv")
    walk.equity_curve.to_csv(output_dir / "walk_forward_equity_curve.csv")
    walk.windows.to_csv(output_dir / "walk_forward_windows.csv", index=False)
    walk.factor_weights.to_csv(output_dir / "walk_forward_factor_weights.csv")

    if benchmark_prices is not None:
        benchmark_returns = benchmark_prices.pct_change()
        capm = capm_regression(
            result.returns,
            benchmark_returns,
            risk_free_rate=backtest_config.get("risk_free_rate", 0.0),
        )
        capm.to_frame("value").to_csv(output_dir / "capm_regression.csv")
        regimes = classify_market_regimes(
            benchmark_prices,
            moving_average_days=regime_config.get("moving_average_days", 200),
            volatility_lookback_days=regime_config.get("volatility_lookback_days", 21),
            volatility_quantile_window=regime_config.get("volatility_quantile_window", 252),
            high_volatility_quantile=regime_config.get("high_volatility_quantile", 0.60),
        )
        regime_summaries = performance_by_regime(result.returns, result.equity_curve, result.turnover, regimes)
        for name, table in regime_summaries.items():
            table.to_csv(output_dir / f"{name}_summary.csv")

    plot_equity_curve(result.equity_curve, output_dir / "equity_curve.png")
    plot_drawdown(result.equity_curve, output_dir / "drawdown.png")
    plot_rolling_metrics(rolling, output_dir / "rolling_metrics.png")
    plot_factor_diagnostics(factor_summary, output_dir / "factor_diagnostics.png")
    if benchmark_prices is not None:
        plot_regime_performance(regime_summaries["combined_regime"], output_dir / "regime_performance.png")

    print("Backtest complete.")
    print(summary.to_string(float_format=lambda value: f"{value:0.4f}"))
    print(f"Reports written to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
