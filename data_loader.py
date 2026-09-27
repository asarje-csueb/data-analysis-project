import pandas as pd
import streamlit as st

from config import DATA_PATH


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df["Urban/Rural"] = df["RuralUrbanIndicator"].map({"U": "Urban", "R": "Rural"})
    df["Franchise"] = df["Is_Franchise"].map({1: "Franchise", 0: "Independent"})
    df["ZIP"] = df["BusinessZip"].astype(str)
    return df
