# Equity Signal Platform

A compact Python research platform for downloading equity data, building cross-sectional factor signals, backtesting simple systematic portfolios, and visualizing results.

This project is designed for quant research recruiting conversations. It favors readable methodology, out-of-sample evaluation, and defensible assumptions over production trading complexity. It is a research and simulation tool only, not a live trading bot.

## What It Does

- Downloads adjusted daily prices with `yfinance`
- Defines a starter large-cap U.S. equity universe
- Computes momentum, volatility, trend, and mean reversion signals
- Combines factor ranks into a simple composite score
- Builds equal-weight or inverse-volatility portfolios
- Runs a monthly rebalance backtest with transaction costs and slippage
- Reports total return, annualized return, volatility, Sharpe ratio, max drawdown, and turnover
- Runs rolling walk-forward train/test evaluations
- Classifies bull/bear and high/low volatility market regimes using SPY
- Computes rolling Sharpe, volatility, drawdown, and turnover
- Evaluates factor hit rate, information coefficient, decay, persistence, and dispersion
- Estimates CAPM alpha/beta and supports generic factor regression inputs
- Runs lightweight config-driven experiments and compares results
- Produces equity curve and drawdown plots
- Includes a Streamlit dashboard for strategy analytics, regimes, factor diagnostics, and experiment comparison

## Project Structure

```text
equity-signal-platform/
├── config/
│   └── default.yaml
├── examples/
│   └── run_backtest.py
├── src/
│   └── equity_signal_platform/
│       ├── analytics/
│       ├── backtesting/
│       ├── config.py
│       ├── data/
│       ├── experiments/
│       ├── portfolio/
│       ├── reporting/
│       ├── signals/
│       └── universe.py
├── streamlit_app/
│   └── app.py
├── tests/
├── requirements.txt
└── README.md
```

## Installation

```bash
git clone https://github.com/johnA750/Equity-Signal-Platform.git
cd Equity-Signal-Platform
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

## Run A Backtest

```bash
python examples/run_backtest.py --config config/default.yaml
```

Outputs are written to `reports/`:

- `backtest_results.csv`
- `performance_summary.csv`
- `latest_signal_ranks.csv`
- `equity_curve.png`
- `drawdown.png`
- `rolling_metrics.csv`
- `factor_summary.csv`
- `capm_regression.csv`
- `walk_forward_returns.csv`
- `*_regime_summary.csv`

## Run Experiments

The default config includes three simple experiment definitions. Run them with:

```bash
python examples/run_experiments.py --config config/default.yaml
```

Outputs are written to `reports/experiments/`:

- `experiment_comparison.csv`
- Per-experiment `summary.csv`
- Per-experiment `returns.csv`
- Per-experiment `rolling_metrics.csv`
- Per-experiment `metadata.json`

## Launch The Dashboard

```bash
streamlit run streamlit_app/app.py
```

The dashboard can run a fresh backtest from the configured universe and display:

- Strategy analytics: performance metrics, equity curve, walk-forward curve, rolling metrics, CAPM table
- Regime analysis: bull/bear and volatility-regime performance
- Factor diagnostics: IC, hit rate, persistence, dispersion, and current rankings
- Experiment comparison: config-driven strategy variants side by side

## Methodology

The default strategy is a monthly rebalanced long-only factor portfolio. The research workflow separates signal estimation, portfolio construction, simulation, diagnostics, and experiment comparison.

1. Daily adjusted close prices are downloaded from Yahoo Finance through `yfinance`.
2. Daily returns are calculated from adjusted prices.
3. Factor signals are estimated from information available at each date:
   - Momentum: trailing return over a configurable lookback, skipping the most recent month by default.
   - Volatility: trailing realized volatility, ranked lower-is-better.
   - Trend: price versus moving average.
   - Mean reversion: short-term trailing return, ranked lower-is-better.
4. On each month-end rebalance date, stocks are ranked by a composite of normalized factor ranks.
5. The top-ranked securities are selected.
6. Portfolio weights are formed using either equal weight or inverse volatility.
7. Weights selected at a rebalance are applied to future daily returns until the next rebalance.
8. Transaction costs and slippage are charged based on portfolio turnover at each rebalance.

The backtest shifts holdings forward after rebalance calculations so signal values are not applied to returns from the same close that produced the signal.

### Walk-Forward Evaluation

Walk-forward testing estimates factor weights from a rolling training window and applies those fixed weights to the next test window. The default setup trains on 36 months and tests on the next 12 months. Factor weights are estimated from positive historical information coefficients. Test-window returns are concatenated into an out-of-sample equity curve.

### Regime Analysis

The platform downloads SPY as the default benchmark. Bull/bear regimes are classified by whether SPY is above or below its moving average. Volatility regimes compare short-term realized volatility to a rolling historical quantile. Strategy performance is then summarized by market, volatility, and combined regimes.

### Factor Diagnostics

Factor diagnostics are cross-sectional and intentionally simple:

- Information coefficient: Spearman rank correlation between signal scores and forward returns
- Hit rate: frequency that top-half ranked names outperform bottom-half ranked names
- Factor decay: average IC across several forward-return horizons
- Signal persistence: rank autocorrelation across configurable lags
- Dispersion: cross-sectional standard deviation of signal scores

### Regression Analysis

CAPM regression estimates annualized alpha, market beta, R-squared, and t-statistics versus benchmark returns. A generic factor regression helper is included for user-supplied factor return data such as Fama-French factors.

### Experiment Framework

Experiments are defined in `config/default.yaml`. Each experiment overrides selected base settings, runs the same research workflow, saves metadata, and contributes to a comparison table. This keeps strategy variants reproducible without adding heavyweight infrastructure.

## Limitations

- Yahoo Finance data may contain survivorship bias, missing data, stale prices, or adjusted price revisions.
- The starter universe is static and does not model index membership changes through time.
- Walk-forward tests reduce overfitting risk but do not eliminate data snooping.
- CAPM and factor regressions are historical estimates and depend on model assumptions.
- The model is long-only and does not include borrow costs, shorting constraints, taxes, market impact, or capacity analysis.
- Transaction cost and slippage assumptions are simplified.
- Results are for research and education. They do not imply future performance or guaranteed profitability.

## Future Improvements

- Point-in-time universe membership
- Fundamental and alternative data factors
- Sector and beta neutrality
- Walk-forward validation
- Risk model integration
- More realistic execution simulation
- Parameter sweep and experiment tracking
- Exportable tear sheets

## Development

Run tests with:

```bash
pytest
```
