import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import pydeck as pdk
import seaborn as sns
import streamlit as st
from pydeck.data_utils import compute_view

from config import MAP_COLORS

MAX_GRANT = 10_000_000
BLUE = [31, 119, 180, 170]
ORANGE = [255, 127, 14, 220]
TOOLTIP = (
    "<b>{BusinessName}</b><br/>"
    "{BusinessCity} {ZIP}<br/>"
    "Grant: <b>{grant_label}</b><br/>"
    "{BusinessType}<br/>"
    "<i>{Tags}</i><br/>"
    "<span style='opacity:0.7'>Click the dot for full details</span>"
)


def dollars(x, pos=None):
    if abs(x) >= 1e9:
        return f"${x / 1e9:.1f}B"
    if abs(x) >= 1e6:
        return f"${x / 1e6:.1f}M"
    if abs(x) >= 1e3:
        return f"${x / 1e3:.0f}K"
    return f"${x:.0f}"


def metric_row(items):
    """Show (label, value) pairs side by side as st.metric cards."""
    for column, (label, value) in zip(st.columns(len(items)), items):
        column.metric(label, value)


def metric_of(grants, metric):
    if metric == "Total Grant $":
        return grants.sum()
    if metric == "Average Grant $":
        return grants.mean() if len(grants) else 0
    return len(grants)


def flag_metric(frame, label_to_col, metric):
    return pd.Series({
        label: metric_of(frame.loc[frame[col] == 1, "GrantAmount"], metric)
        for label, col in label_to_col.items()
    })


def histogram(amounts, bins, log_scale):
    fig, ax = plt.subplots(figsize=(10, 4))
    if log_scale and amounts.nunique() > 1:
        edges = np.logspace(np.log10(amounts.min()), np.log10(amounts.max()), bins + 1)
        ax.hist(amounts, bins=edges, color="steelblue", edgecolor="white")
        ax.set_xscale("log")
    else:
        ax.hist(amounts, bins=bins, color="steelblue", edgecolor="white")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(dollars))
    ax.axvline(amounts.median(), color="darkorange", linestyle="--", label="Median")
    ax.set_title("Distribution of Grant Amount")
    ax.set_xlabel("Grant Amount")
    ax.set_ylabel("Number of Grants")
    ax.legend()
    st.pyplot(fig)


def hbar(series, title, xlabel, ylabel, color, kind="dollars"):
    fig, ax = plt.subplots(figsize=(10, max(3, 0.45 * len(series))))
    sns.barplot(x=series.values, y=series.index, color=color, ax=ax)
    if kind == "percent":
        ax.set_xlim(0, 100)
        ax.xaxis.set_major_formatter(mticker.PercentFormatter())
        for i, value in enumerate(series.values):
            ax.text(value + 1, i, f"{value:.0f}%", va="center")
    elif kind == "count":
        ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    else:
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(dollars))
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    st.pyplot(fig)


def start_view(points):
    """Center and zoom the map on the points, falling back to street level for a single spot."""
    if len(points) > 1 and points[["Latitude", "Longitude"]].nunique().min() > 1:
        view = compute_view(points[["Longitude", "Latitude"]].values.tolist())
        if np.isfinite(view.zoom):
            return pdk.ViewState(latitude=view.latitude, longitude=view.longitude, zoom=view.zoom)
    return pdk.ViewState(
        latitude=points["Latitude"].mean(), longitude=points["Longitude"].mean(), zoom=13
    )


def grant_map(frame, color_by, key):
    """One dot per grant, sized by grant amount and optionally colored by a yes/no column.

    Dots keep a fixed on-screen size (3 px up to 18 px for the $10M cap) at every zoom level.
    Sizing in meters makes dots grow as fast as the map when zooming, so nearby grants merge
    into one blob instead of separating.

    Returns the LoanNumber of the clicked dot, or None when nothing is selected.
    """
    points = frame[[
        "LoanNumber", "BusinessName", "BusinessCity", "ZIP", "Latitude", "Longitude",
        "GrantAmount", "BusinessType", "Tags",
    ]].copy()
    points["grant_label"] = points["GrantAmount"].map(dollars)
    points["radius"] = 3 + 15 * np.sqrt(points["GrantAmount"] / MAX_GRANT)

    highlight = frame[MAP_COLORS[color_by]] == 1 if color_by != "None" else np.zeros(len(frame), bool)
    points["color"] = [ORANGE if h else BLUE for h in highlight]

    layer = pdk.Layer(
        "ScatterplotLayer",
        points,
        id=key,
        get_position=["Longitude", "Latitude"],
        get_radius="radius",
        radius_units=pdk.types.String("pixels"),
        get_fill_color="color",
        stroked=True,
        get_line_color=[255, 255, 255, 120],
        line_width_min_pixels=0.5,
        pickable=True,
        auto_highlight=True,
    )
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=start_view(points),
        map_style=None,
        tooltip={"html": TOOLTIP, "style": {"maxWidth": "320px", "fontSize": "13px"}},
    )
    event = st.pydeck_chart(deck, on_select="rerun", selection_mode="single-object", key=key)
    selected = event.selection.objects.get(key, [])
    return selected[0]["LoanNumber"] if selected else None
