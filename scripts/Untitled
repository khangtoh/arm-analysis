#!/usr/bin/env python3
"""
ARM AI/GPU Timeline Overlay (replicable)

What it does
- Downloads exact historical prices for ARM (daily OHLCV) via yfinance
- Overlays key AI/GPU/strategy milestones as vertical lines + labels
- Computes event-window returns (e.g., -5d to +5d) and saves a CSV
- Saves a high-res PNG chart

Usage
  pip install -U yfinance pandas numpy matplotlib
  python arm_ai_timeline_overlay.py --ticker ARM --start 2023-09-01 --end 2026-01-17 --window 5

Notes
- yfinance uses Yahoo Finance. For “official” pricing, replace the data loader with your vendor.
"""

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

try:
    import yfinance as yf
except ImportError as e:
    raise SystemExit(
        "Missing dependency: yfinance\n"
        "Install with: pip install -U yfinance pandas numpy matplotlib\n"
    ) from e


@dataclass(frozen=True)
class Event:
    date: str   # YYYY-MM-DD
    label: str


DEFAULT_EVENTS = [
    Event("2023-09-14", "IPO (AI optionality)"),
    Event("2024-05-30", "Immortalis GPU (edge AI narrative)"),
    Event("2024-07-10", "AI enthusiasm peak (approx)"),
    Event("2025-02-05", "Earnings/guidance (AI not enough)"),
    Event("2025-02-14", "Meta custom chip news (FT/Reuters window)"),
    Event("2026-01-13", "Analyst downgrade / sustainability concerns"),
]


def nearest_trading_day_index(idx: pd.DatetimeIndex, d: pd.Timestamp) -> pd.Timestamp:
    """
    Map a calendar date to the nearest trading day on/after that date.
    If the date is beyond the index range, clamps to last available date.
    """
    if len(idx) == 0:
        raise ValueError("Empty price index")
    if d <= idx[0]:
        return idx[0]
    if d >= idx[-1]:
        return idx[-1]
    # find first trading day on/after d
    pos = idx.searchsorted(d, side="left")
    return idx[pos]


def download_prices(ticker: str, start: str, end: str) -> pd.DataFrame:
    """
    Download daily OHLCV. auto_adjust=False to keep raw prices (you can toggle).
    """
    df = yf.download(ticker, start=start, end=end, interval="1d", auto_adjust=False, progress=False)
    if df is None or df.empty:
        raise RuntimeError(f"No data returned for {ticker}. Check ticker or date range.")
    # yfinance sometimes returns multi-index columns for multiple tickers; normalize
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.sort_index()
    return df


def compute_event_returns(close: pd.Series, events: list[Event], window: int) -> pd.DataFrame:
    """
    For each event date:
      - find nearest trading day on/after event date
      - compute returns from t-window to t+window
    """
    rows = []
    idx = close.index
    for ev in events:
        ev_date = pd.to_datetime(ev.date)
        t0 = nearest_trading_day_index(idx, ev_date)

        # compute window bounds using trading-day offsets
        i0 = idx.get_loc(t0)
        i_pre = max(0, i0 - window)
        i_post = min(len(idx) - 1, i0 + window)

        t_pre = idx[i_pre]
        t_post = idx[i_post]

        p_pre = float(close.loc[t_pre])
        p0 = float(close.loc[t0])
        p_post = float(close.loc[t_post])

        rows.append(
            {
                "event_label": ev.label,
                "event_date_calendar": ev_date.date().isoformat(),
                "event_date_trading": t0.date().isoformat(),
                f"close_t-{window}d": p_pre,
                "close_t0": p0,
                f"close_t+{window}d": p_post,
                f"ret_t-{window}d_to_t0": (p0 / p_pre - 1.0) if p_pre else np.nan,
                f"ret_t0_to_t+{window}d": (p_post / p0 - 1.0) if p0 else np.nan,
                f"ret_t-{window}d_to_t+{window}d": (p_post / p_pre - 1.0) if p_pre else np.nan,
            }
        )

    out = pd.DataFrame(rows)
    # nicer % formatting columns (keep numeric for CSV; formatting for printing)
    return out


def plot_with_events(
    close: pd.Series,
    events: list[Event],
    out_png: str,
    title: str,
    annotate_y_frac: float = 0.96,
):
    """
    Plot close price with vertical lines at event dates (mapped to trading days).
    """
    idx = close.index
    y_top = close.max() * annotate_y_frac

    plt.figure(figsize=(14, 6))
    plt.plot(idx, close.values, linewidth=2, label="Close")

    for ev in events:
        ev_date = pd.to_datetime(ev.date)
        t0 = nearest_trading_day_index(idx, ev_date)
        plt.axvline(t0, linestyle="--", alpha=0.6)
        plt.text(
            t0,
            y_top,
            f"{ev.label}\n({t0.date().isoformat()})",
            rotation=90,
            fontsize=8,
            va="top",
            ha="right",
        )

    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=220)
    plt.close()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--ticker", default="ARM", help="Ticker symbol (default: ARM)")
    p.add_argument("--start", default="2023-09-01", help="Start date YYYY-MM-DD")
    p.add_argument("--end", default=None, help="End date YYYY-MM-DD (default: today)")
    p.add_argument("--window", type=int, default=5, help="Event window in trading days (default: 5)")
    p.add_argument("--out_png", default="arm_ai_timeline_overlay.png", help="Output PNG filename")
    p.add_argument("--out_csv", default="arm_ai_event_returns.csv", help="Output CSV filename")
    return p.parse_args()


def main():
    args = parse_args()
    end = args.end or datetime.now().date().isoformat()

    prices = download_prices(args.ticker, args.start, end)
    close = prices["Close"].dropna()

    events = DEFAULT_EVENTS

    # Outputs
    title = f"{args.ticker} — Stock Price vs AI/GPU Narrative Timeline"
    plot_with_events(
        close=close,
        events=events,
        out_png=args.out_png,
        title=title,
    )

    ev_table = compute_event_returns(close, events, window=args.window)
    ev_table.to_csv(args.out_csv, index=False)

    # Console summary
    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 50)
    print(f"Saved chart: {args.out_png}")
    print(f"Saved event returns table: {args.out_csv}\n")
    print(ev_table)


if __name__ == "__main__":
    main()
