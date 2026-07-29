"""Themed Plotly figures for the Pints and Plans tabs."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.theme import Palette, plotly_layout


def _finish(figure: go.Figure, palette: Palette, height: int, title: str = "") -> go.Figure:
    """Apply the shared palette-driven layout to a figure."""
    figure.update_layout(**plotly_layout(palette), height=height, title=title or None)
    return figure


def leaderboard_bar(frame: pd.DataFrame, palette: Palette) -> go.Figure:
    """Horizontal bar chart of total pints per lad.

    Args:
        frame: Columns ``name``, ``total``, ``today``.
        palette: Active palette.
    """
    ordered = frame.sort_values("total")
    figure = px.bar(
        ordered,
        x="total",
        y="name",
        orientation="h",
        text="total",
        color="total",
        color_continuous_scale=[palette.accent, palette.primary],
        labels={"total": "Pints", "name": ""},
    )
    figure.update_traces(
        textposition="outside",
        cliponaxis=False,
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>%{x} pints<extra></extra>",
    )
    figure.update_coloraxes(showscale=False)
    return _finish(figure, palette, 60 + 44 * max(1, len(ordered)), "Pint League standings")


def daily_area(frame: pd.DataFrame, palette: Palette) -> go.Figure:
    """Stacked area chart of pints per day per lad.

    Args:
        frame: Columns ``day``, ``name``, ``pints``.
        palette: Active palette.
    """
    figure = px.area(
        frame,
        x="day",
        y="pints",
        color="name",
        line_shape="spline",
        color_discrete_sequence=list(palette.chart_sequence),
        labels={"day": "", "pints": "Pints", "name": ""},
    )
    figure.update_traces(hovertemplate="<b>%{fullData.name}</b><br>%{y} pints on %{x|%a %d %b}<extra></extra>")
    return _finish(figure, palette, 330, "Daily consumption curve")


def drinks_scatter(frame: pd.DataFrame, palette: Palette) -> go.Figure:
    """Scatter timeline of every logged pint by hour of day.

    Args:
        frame: Columns ``consumed_at``, ``name``, ``venue``.
        palette: Active palette.
    """
    figure = px.scatter(
        frame,
        x="consumed_at",
        y="name",
        color="name",
        size=[9] * len(frame),
        hover_data={"venue": True, "consumed_at": "|%a %d %b %H:%M", "name": False},
        color_discrete_sequence=list(palette.chart_sequence),
        labels={"consumed_at": "", "name": ""},
    )
    figure.update_traces(marker=dict(line=dict(width=1, color=palette.bg), opacity=0.9), showlegend=False)
    return _finish(figure, palette, 300, "Every pint, plotted")



def itinerary_gantt(frame: pd.DataFrame, palette: Palette) -> go.Figure:
    """Calendar-style timeline of activities.

    Args:
        frame: Columns ``start``, ``end``, ``title``, ``day_label``, ``category``.
        palette: Active palette.
    """
    figure = px.timeline(
        frame,
        x_start="start",
        x_end="end",
        y="day_label",
        color="category",
        text="title",
        hover_data={"title": True, "category": True},
        color_discrete_sequence=list(palette.chart_sequence),
        labels={"day_label": "", "category": ""},
    )
    figure.update_yaxes(autorange="reversed")
    figure.update_traces(textposition="inside", insidetextanchor="start", marker_line_width=0)
    return _finish(figure, palette, 130 + 62 * max(1, frame["day_label"].nunique()), "Trip calendar")


def votes_bar(frame: pd.DataFrame, palette: Palette) -> go.Figure:
    """Diverging bar chart of up/down votes per activity idea.

    Args:
        frame: Columns ``title``, ``up``, ``down``.
        palette: Active palette.
    """
    figure = go.Figure()
    figure.add_bar(y=frame["title"], x=frame["up"], name="For", orientation="h",
                   marker_color=palette.success, hovertemplate="%{x} for<extra></extra>")
    figure.add_bar(y=frame["title"], x=-frame["down"], name="Against", orientation="h",
                   marker_color=palette.danger, hovertemplate="%{x} against<extra></extra>")
    figure.update_layout(barmode="relative")
    figure.update_xaxes(title="Votes")
    return _finish(figure, palette, 90 + 40 * max(1, len(frame)), "Where the group stands")
