import pandas as pd
import streamlit as st

from config import DATA_PATH, TAG_COLS


def grant_tags(df):
    """Readable tags per grant, such as 'Women-owned · HUBZone · Rural'."""
    tags = [
        [label for label, col in TAG_COLS.items() if row[col] == 1]
        + (["Rural"] if row["Urban/Rural"] == "Rural" else [])
        for _, row in df.iterrows()
    ]
    return pd.Series([" · ".join(t) or "No ownership or community flags" for t in tags], index=df.index)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df["Urban/Rural"] = df["RuralUrbanIndicator"].map({"U": "Urban", "R": "Rural"})
    df["Franchise"] = df["Is_Franchise"].map({1: "Franchise", 0: "Independent"})
    df["ZIP"] = df["BusinessZip"].astype(str)
    df["BusinessType"] = df["RestaurantType"].str.replace(" && ", ", ")
    df["Tags"] = grant_tags(df)
    return df
