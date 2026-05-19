# GLD Event Study Dashboard

Interactive quant research demo for a data engineer / quant data engineer interview.

The dashboard studies a simple drawdown event in `GLD`:

> If GLD falls more than 5% over the previous 5 trading days, what has the 3-day forward return historically looked like?

It downloads daily OHLCV data, calculates point-in-time event labels, computes forward returns and event-level Sharpe, and writes a single static HTML file with the GLD price and volume JSON embedded directly in the page.

## Why This Demo Fits A Quant Data Engineer Role

- Market data ingestion from a reproducible source
- Time-series feature engineering with rolling 5-day drawdown
- Point-in-time event labeling with no look-ahead in the signal definition
- Forward return analysis and event-level Sharpe calculation
- Baseline comparison, excess return, t-stat, and event-level Sharpe calculation
- Interactive research UI with zoom, hover tooltips, event highlighting, parameter controls, and click-to-zoom event rows
- Non-overlapping event sampling to avoid overstating clustered drawdowns
- Average event-window path from pre-event drawdown through post-event holding period
- Static deployment: no API key, no database, no backend required after generation

## Quick Start

```powershell
python -m pip install -r requirements.txt
python scripts/build_dashboard.py
python -m pytest
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/web/
```

For GitHub Pages, serve the repository root. The root `index.html` redirects to the dashboard in `web/`.

## Outputs

- `data/gld_daily.csv`: downloaded GLD OHLCV history
- `web/index.html`: static dashboard with embedded JSON data

## Metric Notes

The displayed Sharpe is an event-level metric:

```text
mean(3-day forward returns after trigger) / std(3-day forward returns after trigger)
```

This is an event study, not a fully executable portfolio backtest. Overlapping events, capital allocation, slippage, and transaction costs are intentionally separated from the first-pass research question.

The dashboard defaults to non-overlapping events. You can switch to all triggers or first-in-cluster sampling to show how event definitions affect sample count and inference.

## Data Source

Daily GLD OHLCV data is first attempted from Stooq's historical CSV endpoint. If Stooq asks for an API key, the generator falls back to Yahoo Finance's chart endpoint and still writes the final GLD data into the HTML:

```text
https://stooq.com/q/d/l/?s=gld.us&i=d
https://query1.finance.yahoo.com/v8/finance/chart/GLD
```
