import pandas as pd
import streamlit as st

from charts import dollars, flag_metric, grant_map, hbar, histogram, metric_row
from config import (
    FLAG_GROUPS, GROUP_BY_OPTIONS, GROUP_COLS, MAP_COLORS, METRICS, PURPOSE_COLS, SUMMARY_LABELS,
    TABLE_COLS,
)


def section_header(title, description):
    st.divider()
    st.subheader(title)
    st.write(description)


def render_kpis(df, filtered):
    metric_row([
        ("Number of Grants", f"{len(filtered):,}"),
        ("Total Grant Dollars", dollars(filtered["GrantAmount"].sum())),
        ("Median Grant", dollars(filtered["GrantAmount"].median())),
        ("Women-owned Share", f"{filtered['WomenOwnedIndicator'].mean() * 100:.1f}%"),
    ])
    st.caption(f"Showing {len(filtered):,} of {len(df):,} grants based on the current filters.")


def render_grant_size(filtered):
    section_header("1. How large were the grants?", "Distribution of grant amounts for the selected businesses.")
    bins_col, log_col = st.columns(2)
    bins = bins_col.slider("Number of Bins", 5, 50, 30)
    log_scale = log_col.checkbox(
        "Log scale (x-axis)", value=True,
        help="Grants range from about $1K to $10M. A log scale spreads out the smaller grants.",
    )
    histogram(filtered["GrantAmount"], bins, log_scale)
    st.caption("Each bar counts how many grants fall in that dollar range. The dashed orange line marks the median grant.")


def segment_values(filtered, group_by, metric):
    """Grant total, average, or count for each segment of the chosen grouping, largest first."""
    if group_by in FLAG_GROUPS:
        segment = flag_metric(filtered, FLAG_GROUPS[group_by], metric)
    else:
        column = GROUP_COLS[group_by]
        grouped = filtered.groupby(column)["GrantAmount"]
        segment = grouped.size() if metric == "Number of Grants" else (
            grouped.sum() if metric == "Total Grant $" else grouped.mean()
        )
        if group_by.startswith("Top 15"):
            segment = segment[segment.index.isin(filtered[column].value_counts().head(15).index)]
    return segment[segment > 0].sort_values(ascending=False)


def render_segments(filtered):
    section_header("2. Which businesses received the most funding?", "Compare grant funding across business segments.")
    group_col, metric_col = st.columns(2)
    group_by = group_col.selectbox("Group by", GROUP_BY_OPTIONS)
    metric = metric_col.radio("Metric", METRICS, horizontal=True)

    hbar(
        segment_values(filtered, group_by, metric), f"{metric} by {group_by}", metric, group_by,
        "seagreen", kind="count" if metric == "Number of Grants" else "dollars",
    )
    if group_by in FLAG_GROUPS:
        st.caption(
            f"A business can belong to more than one {group_by.lower()}, "
            "so bar totals can add up to more than the overall total."
        )
    else:
        st.caption("Longer bars mean more funding for that segment.")


def render_purposes(filtered):
    section_header("3. What uses of RRF funds were reported?", "Share of selected grants that reported each intended use of funds.")
    purpose_share = filtered[list(PURPOSE_COLS)].mean() * 100
    purpose_share.index = [PURPOSE_COLS[c] for c in purpose_share.index]
    if st.checkbox("Sort purposes from most to least common", value=True):
        purpose_share = purpose_share.sort_values(ascending=False)
    hbar(purpose_share, "Grant Purpose (% of Grants)", "Percent of Grants", "Grant Purpose", "slateblue", kind="percent")
    st.caption("Recipients could select more than one purpose, so percentages do not add up to 100%.")


def render_grant_details(frame, loan_number):
    """Details card for the grant clicked on a map."""
    match = frame[frame["LoanNumber"] == loan_number]
    if match.empty:
        return
    grant = match.iloc[0]
    entity = grant["LegalOrganizationType"]
    if grant["Is_Franchise"] == 1:
        entity += f" · {grant['FranchiseName']} franchise"
    purposes = [label for col, label in PURPOSE_COLS.items() if grant[col] == 1]

    with st.container(border=True):
        st.markdown(f"#### {grant['BusinessName']}")
        approved = pd.to_datetime(grant["ApprovalDate"]).strftime("%B %-d, %Y")
        st.caption(
            f"{grant['BusinessAddress']}, {grant['BusinessCity']}, CA {grant['ZIP']} · Approved {approved}"
        )
        metric_row([
            ("Grant Amount", dollars(grant["GrantAmount"])),
            ("Area", grant["Urban/Rural"]),
        ])
        st.markdown(f"**Business type:** {grant['BusinessType']}")
        st.markdown(f"**Entity:** {entity}")
        st.markdown(f"**Ownership and community:** {grant['Tags']}")
        st.markdown(f"**Reported uses of the grant:** {', '.join(purposes)}")


def show_selection(frame, loan_number, hint):
    if loan_number is None:
        st.caption(hint)
    else:
        render_grant_details(frame, loan_number)


def render_map(filtered):
    """Draw the grant map and return the highlight choice so the city profile can reuse it."""
    section_header(
        "4. Where did the grants go?",
        "Each dot is one grant. Larger dots are larger grants. Hover over a dot for a quick "
        "summary, click it for full details, and zoom in to separate nearby dots.",
    )
    color_by = st.selectbox("Highlight in orange", ["None", *MAP_COLORS])
    selected = grant_map(filtered, color_by, key="state_map")
    if color_by != "None":
        share = filtered[MAP_COLORS[color_by]].mean() * 100
        st.caption(f"Orange dots are {color_by} grants ({share:.1f}% of the selected grants). Blue dots are all others.")
    show_selection(
        filtered, selected,
        "Click any dot to see that grant's details here. "
        "Use the City and ZIP Code filters in the sidebar to zoom in on an area.",
    )
    return color_by


def zip_table(city_df):
    summary = city_df.groupby("ZIP").agg(
        Grants=("GrantAmount", "size"),
        Total=("GrantAmount", "sum"),
        Median=("GrantAmount", "median"),
        WomenOwned=("WomenOwnedIndicator", "mean"),
        LowIncome=("LMIIndicator", "mean"),
    ).sort_values("Total", ascending=False)
    summary[["Total", "Median"]] = summary[["Total", "Median"]].map(dollars)
    st.dataframe(
        summary,
        column_config={
            "Total": "Total $",
            "Median": "Median $",
            "WomenOwned": st.column_config.ProgressColumn("Women-owned", format="percent", min_value=0, max_value=1),
            "LowIncome": st.column_config.ProgressColumn("Low-income area", format="percent", min_value=0, max_value=1),
        },
    )


def render_city_profile(filtered, color_by):
    section_header(
        "5. City profile",
        "Pick a city to see its headline numbers and how funding was spread across its ZIP codes.",
    )
    city_counts = filtered["BusinessCity"].value_counts()
    city = st.selectbox(
        "City", city_counts.index, format_func=lambda c: f"{c} ({city_counts[c]:,} grants)"
    )
    city_df = filtered[filtered["BusinessCity"] == city]

    metric_row([
        ("Grants", f"{len(city_df):,}"),
        ("Total $", dollars(city_df["GrantAmount"].sum())),
        ("Median Grant", dollars(city_df["GrantAmount"].median())),
        ("Share of $", f"{city_df['GrantAmount'].sum() / filtered['GrantAmount'].sum() * 100:.1f}%"),
    ])
    map_col, table_col = st.columns(2)
    with map_col:
        selected = grant_map(city_df, color_by, key="city_map")
    with table_col:
        zip_table(city_df)
    st.caption(
        "Share of $ is this city's portion of all selected grant dollars. "
        "The table lists every ZIP code in the city, sorted by total grant dollars."
    )
    show_selection(city_df, selected, "Click a dot on the city map to see that grant's details here.")


def render_summary(filtered):
    section_header("Summary Statistics", "Grant amount statistics for the selected businesses.")
    stats = filtered["GrantAmount"].describe()
    values = [f"{v:,.0f}" if k == "count" else f"${v:,.0f}" for k, v in stats.items()]
    st.dataframe(
        pd.DataFrame({"Statistic": stats.index.map(SUMMARY_LABELS), "Grant Amount": values}),
        hide_index=True,
    )
    with st.expander("View filtered data"):
        st.dataframe(
            filtered[TABLE_COLS].sort_values("GrantAmount", ascending=False),
            hide_index=True,
        )
