from __future__ import annotations

import argparse
from pathlib import Path

from equity_signal_platform.config import PlatformConfig
from equity_signal_platform.data import download_adjusted_prices
from equity_signal_platform.experiments import run_experiments
from equity_signal_platform.universe import get_universe


def main() -> None:
    parser = argparse.ArgumentParser(description="Run configured equity research experiments.")
    parser.add_argument("--config", default="config/default.yaml", help="Path to YAML config file.")
    args = parser.parse_args()

    config = PlatformConfig.from_yaml(args.config)
    raw = config.raw
    data_config = config.section("data")
    universe_config = config.section("universe")
    experiment_config = config.section("experiments")
    regime_config = config.section("regime")

    output_dir = Path(experiment_config.get("output_dir", "reports/experiments"))
    tickers = sorted(set(get_universe(universe_config) + [regime_config.get("benchmark_ticker", "SPY")]))
    prices = download_adjusted_prices(
        tickers=tickers,
        start=data_config.get("start_date", "2018-01-01"),
        end=data_config.get("end_date"),
        auto_adjust=data_config.get("auto_adjust", True),
        cache_path=output_dir / "experiment_prices.csv",
    )
    benchmark_ticker = regime_config.get("benchmark_ticker", "SPY")
    benchmark_prices = prices[benchmark_ticker] if benchmark_ticker in prices else None
    research_prices = prices.drop(columns=[benchmark_ticker], errors="ignore")

    comparison = run_experiments(raw, research_prices, benchmark_prices, output_dir)
    print("Experiment run complete.")
    print(comparison.to_string(float_format=lambda value: f"{value:0.4f}"))
    print(f"Experiment outputs written to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
