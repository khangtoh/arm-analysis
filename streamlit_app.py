import datetime
from typing import List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from scripts.arm_ai_timeline_overlay import (
    DEFAULT_EVENTS,
    compute_event_returns,
    download_prices,
    nearest_trading_day_index,
)


@st.cache_data(show_spinner=False)
def load_prices(ticker: str, start: str, end: str) -> pd.Series:
    prices = download_prices(ticker, start, end)
    return prices["Close"].dropna()


def plot_with_events_figure(close: pd.Series, events: List, title: str) -> go.Figure:
    idx = close.index
    y_top = close.max() * 0.96

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=idx,
            y=close.values,
            mode="lines",
            line=dict(width=2),
            name="Close",
        )
    )

    for ev in events:
        ev_date = pd.to_datetime(ev.date)
        t0 = nearest_trading_day_index(idx, ev_date)
        fig.add_vline(x=t0, line_dash="dash", opacity=0.6)
        fig.add_annotation(
            x=t0,
            y=y_top,
            text=f"{ev.label}<br>({t0.date().isoformat()})",
            textangle=-90,
            showarrow=False,
            xanchor="right",
            yanchor="top",
            font=dict(size=10),
        )

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def main() -> None:
    st.set_page_config(page_title="ARM AI/GPU Timeline Overlay", layout="wide")
    st.title("ARM AI/GPU Timeline Overlay")
    st.write(
        "Explore how ARM's price action aligns with key AI/GPU narrative milestones. "
        "Adjust the date range and event window to update the overlay and returns table."
    )

    with st.sidebar:
        st.header("Controls")
        ticker = st.text_input("Ticker", value="ARM")
        default_start = datetime.date(2023, 9, 1)
        default_end = datetime.date.today()
        start_date = st.date_input("Start date", value=default_start)
        end_date = st.date_input("End date", value=default_end)
        window = st.number_input("Event window (trading days)", min_value=1, max_value=30, value=5)
        run = st.button("Run analysis")

    if not run:
        st.info("Set your parameters and click **Run analysis**.")
        return

    if start_date >= end_date:
        st.error("Start date must be before end date.")
        return

    with st.spinner("Downloading prices and computing event returns..."):
        close = load_prices(ticker, start_date.isoformat(), end_date.isoformat())
        events = DEFAULT_EVENTS
        fig = plot_with_events_figure(
            close=close,
            events=events,
            title=f"{ticker} — Stock Price vs AI/GPU Narrative Timeline",
        )
        returns = compute_event_returns(close, events, window=int(window))

    st.subheader("Timeline overlay")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Event-window returns")
    st.dataframe(returns, use_container_width=True)

    with st.expander("Milestone events"):
        st.markdown("""The current milestones are sourced from `DEFAULT_EVENTS` in the analysis script.""")
        st.table(pd.DataFrame([{"date": ev.date, "label": ev.label} for ev in events]))


if __name__ == "__main__":
    main()
