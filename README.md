# Equity Signal Platform

A compact Python research platform for downloading equity data, building cross-sectional factor signals, backtesting simple systematic portfolios, and visualizing results.

This project is designed for quant research recruiting conversations. It favors readable methodology and defensible assumptions over production trading complexity. It is a research and simulation tool only, not a live trading bot.

## What It Does

- Downloads adjusted daily prices with `yfinance`
- Defines a starter large-cap U.S. equity universe
- Computes momentum, volatility, trend, and mean reversion signals
- Combines factor ranks into a simple composite score
- Builds equal-weight or inverse-volatility portfolios
- Runs a monthly rebalance backtest with transaction costs and slippage
- Reports total return, annualized return, volatility, Sharpe ratio, max drawdown, and turnover
- Produces equity curve and drawdown plots
- Includes a Streamlit dashboard for metrics, charts, and current top-ranked names

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

## Launch The Dashboard

```bash
streamlit run streamlit_app/app.py
```

The dashboard can run a fresh backtest from the configured universe and display:

- Performance metrics
- Equity curve
- Drawdown
- Current top-ranked factor signals

## Methodology

The default strategy is a monthly rebalanced long-only factor portfolio.

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

## Limitations

- Yahoo Finance data may contain survivorship bias, missing data, stale prices, or adjusted price revisions.
- The starter universe is static and does not model index membership changes through time.
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
