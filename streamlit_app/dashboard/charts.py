from __future__ import annotations

import calendar

import pandas as pd
import plotly.graph_objects as go


TEMPLATE = "plotly_white"
BLUE = "#2454a6"
GREEN = "#0f766e"
RED = "#b42318"
GOLD = "#b7791f"


def _layout(fig: go.Figure, title: str, height: int = 380) -> go.Figure:
    fig.update_layout(
        title=title,
        template=TEMPLATE,
        height=height,
        margin=dict(l=20, r=20, t=55, b=35),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def equity_curve(context: dict) -> go.Figure:
    result = context["result"]
    walk = context["walk"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=result.equity_curve.index, y=result.equity_curve, mode="lines", name="Backtest"))
    if not walk.equity_curve.empty:
        fig.add_trace(go.Scatter(x=walk.equity_curve.index, y=walk.equity_curve, mode="lines", name="Walk-Forward OOS"))
    return _layout(fig, "Equity Curve", 420)


def drawdown(equity_curve: pd.Series) -> go.Figure:
    dd = equity_curve / equity_curve.cummax() - 1.0
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dd.index, y=dd, fill="tozeroy", mode="lines", name="Drawdown", line=dict(color=RED)))
    return _layout(fig, "Drawdown", 320)


def line_chart(frame: pd.DataFrame, columns: list[str], title: str, height: int = 380) -> go.Figure:
    fig = go.Figure()
    for column in columns:
        if column in frame:
            fig.add_trace(go.Scatter(x=frame.index, y=frame[column], mode="lines", name=column.replace("_", " ").title()))
    return _layout(fig, title, height)


def bar_chart(frame: pd.DataFrame, y_columns: list[str], title: str, height: int = 360) -> go.Figure:
    fig = go.Figure()
    for column in y_columns:
        if column in frame:
            fig.add_trace(go.Bar(x=frame.index, y=frame[column], name=column.replace("_", " ").title()))
    fig.update_layout(barmode="group")
    return _layout(fig, title, height)


def monthly_return_heatmap(returns: pd.Series) -> go.Figure:
    monthly = (1.0 + returns).resample("ME").prod() - 1.0
    table = monthly.to_frame("return")
    table["year"] = table.index.year
    table["month"] = table.index.month
    heatmap = table.pivot(index="year", columns="month", values="return")
    heatmap = heatmap.reindex(columns=range(1, 13))
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap.values,
            x=[calendar.month_abbr[i] for i in range(1, 13)],
            y=heatmap.index.astype(str),
            colorscale="RdYlGn",
            zmid=0,
            colorbar=dict(title="Return"),
            hovertemplate="%{y} %{x}<br>Return: %{z:.2%}<extra></extra>",
        )
    )
    return _layout(fig, "Monthly Return Heatmap", 360)


def factor_ic_chart(ic_frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for column in ic_frame.columns:
        fig.add_trace(go.Scatter(x=ic_frame.index, y=ic_frame[column].rolling(63).mean(), mode="lines", name=column))
    return _layout(fig, "Rolling 63-Day Information Coefficient", 380)


def factor_decay_chart(decay_frame: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for factor in decay_frame.index:
        fig.add_trace(go.Scatter(x=decay_frame.columns, y=decay_frame.loc[factor], mode="lines+markers", name=factor))
    return _layout(fig, "Factor Decay", 360)

