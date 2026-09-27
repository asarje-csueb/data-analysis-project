import streamlit as st

from data_loader import load_data
from filters import render_filters
from sections import (
    render_city_profile, render_grant_size, render_kpis, render_map, render_purposes,
    render_segments, render_summary,
)

INTRO = (
    "The Restaurant Revitalization Fund (RRF) gave grants to restaurants and bars hurt by "
    "COVID-19. This app explores **6,077 California grants** to answer four questions: "
    "How large were the grants? Which kinds of businesses received the most money? "
    "Where did the money go? And did the funding reach underserved owners and communities? "
    "Use the **Filters** in the left sidebar to focus on any segment. Every number and "
    "chart on this page updates to match."
)


def main():
    st.set_page_config(page_title="RRF Grant Explorer", layout="wide")
    st.title("SBA Restaurant Revitalization Fund - Grant Explorer")
    st.write(INTRO)

    df = load_data()
    filtered = render_filters(df)
    if filtered.empty:
        st.warning("No grants match the selected filters. Try removing one or more filters.")
        st.stop()

    render_kpis(df, filtered)
    render_grant_size(filtered)
    render_segments(filtered)
    render_purposes(filtered)
    color_by = render_map(filtered)
    render_city_profile(filtered, color_by)
    render_summary(filtered)


main()
