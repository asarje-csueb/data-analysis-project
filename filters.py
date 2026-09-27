import numpy as np
import streamlit as st

from config import OWNERSHIP_COLS, PURPOSE_COLS, RESTAURANT_TYPE_COLS


def any_flag(frame, columns):
    """Keep rows where any of the given 0/1 columns equals 1."""
    if not columns:
        return frame
    return frame[frame[columns].eq(1).any(axis=1)]


def sidebar_isin(frame, label, options, column, **kwargs):
    """Multiselect. An empty selection means no filter."""
    picked = st.sidebar.multiselect(label, options, **kwargs)
    return frame[frame[column].isin(picked)] if picked else frame


def sidebar_flags(frame, label, label_to_col, **kwargs):
    """Multiselect over yes/no columns. A row is kept if any selected flag is 1."""
    picked = st.sidebar.multiselect(label, list(label_to_col), **kwargs)
    return any_flag(frame, [label_to_col[p] for p in picked])


def sidebar_choice(frame, label, options, column, mapping=None, widget="selectbox", **kwargs):
    """Dropdown or radio that starts with 'All' and filters one column."""
    control = st.sidebar.radio if widget == "radio" else st.sidebar.selectbox
    picked = control(label, ["All", *options], **kwargs)
    if picked == "All":
        return frame
    return frame[frame[column] == (mapping[picked] if mapping else picked)]


def sidebar_grant_range(frame, df):
    low, high = int(np.floor(df["GrantAmount"].min())), int(np.ceil(df["GrantAmount"].max()))
    picked = st.sidebar.slider(
        "Grant Amount ($)", low, high, (low, high), step=5000, format="$%d"
    )
    return frame[frame["GrantAmount"].between(*picked)]


def filter_location(frame, df):
    frame = sidebar_isin(
        frame, "City", sorted(df["BusinessCity"].dropna().unique()), "BusinessCity"
    )
    return sidebar_isin(
        frame, "ZIP Code", sorted(frame["ZIP"].unique()), "ZIP",
        help="Only ZIP codes in the selected cities are listed.",
    )


def filter_business(frame):
    frame = sidebar_flags(
        frame, "Restaurant Type", RESTAURANT_TYPE_COLS,
        help="A business can be more than one type. Rows matching any selected type are kept.",
    )
    frame = sidebar_choice(
        frame, "Urban vs Rural", ["Urban", "Rural"], "Urban/Rural", widget="radio", horizontal=True
    )
    frame = sidebar_choice(
        frame, "HUBZone", ["In HUBZone", "Not in HUBZone"], "HubzoneIndicator",
        mapping={"In HUBZone": 1, "Not in HUBZone": 0},
        help="HUBZones are SBA-designated historically underutilized business zones.",
    )
    frame = sidebar_flags(
        frame, "Ownership Type", OWNERSHIP_COLS,
        help="Rows matching any selected ownership type are kept.",
    )
    return sidebar_flags(
        frame, "Grant Purpose", {label: col for col, label in PURPOSE_COLS.items()},
        help="Rows where the recipient listed any selected purpose are kept.",
    )


def filter_entity(frame, df):
    st.sidebar.subheader("Entity Type")
    frame = sidebar_choice(
        frame, "Franchise or Independent", ["Franchise", "Independent"], "Franchise"
    )
    frame = sidebar_isin(
        frame, "Legal Organization Type",
        df["LegalOrganizationType"].value_counts().index.tolist(), "LegalOrganizationType",
    )
    if st.sidebar.checkbox(
        "Only low-income (LMI) communities",
        help="Keep only businesses located in low- and moderate-income (LMI) areas.",
    ):
        frame = frame[frame["LMIIndicator"] == 1]
    return frame


def render_filters(df):
    """Draw every sidebar filter and return the rows that match all of them."""
    st.sidebar.header("Filters")
    st.sidebar.caption("Leave a filter empty (or on 'All') to include everything.")
    filtered = filter_location(df.copy(), df)
    filtered = sidebar_grant_range(filtered, df)
    filtered = filter_business(filtered)
    return filter_entity(filtered, df)
