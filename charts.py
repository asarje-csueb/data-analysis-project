import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

from config import MAP_COLORS


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


def grant_map(frame, color_by="None", scale=0.4):
    """One dot per grant, sized by grant amount and optionally colored by a yes/no column."""
    points = frame[["Latitude", "Longitude", "GrantAmount"]].copy()
    points["size"] = np.sqrt(points["GrantAmount"]) * scale
    points["color"] = "#1f77b4"
    if color_by != "None":
        points["color"] = np.where(frame[MAP_COLORS[color_by]] == 1, "#ff7f0e", "#1f77b4")
    st.map(points, latitude="Latitude", longitude="Longitude", size="size", color="color")
