import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

st.set_page_config(page_title="RRF Grant Explorer", layout="wide")

RESTAURANT_TYPES = [
    "Restaurant",
    "Bar, Saloon, Lounge, Tavern",
    "Caterer",
    "Bakery",
    "Food Stand, Food Truck, Food Cart",
    "Snack and Nonalcoholic Beverage Bar",
    "Brewery and/or microbrewery",
    "Brewpub, Tasting Room, Taproom",
    "Winery",
    "Distillery",
    "Licensed Alcohol Producer",
    "Inn",
    "Other",
]

# Column name -> label a business user sees. "Socioeconmic" is misspelled in the source data.
PURPOSE_COLS = {
    "grant_purpose_payroll": "Payroll",
    "grant_purpose_rent": "Rent / Mortgage",
    "grant_purpose_utility": "Utilities",
    "grant_purpose_food": "Food & Beverage",
    "grant_purpose_supplies": "Supplies",
    "grant_purpose_operations": "Operations",
    "grant_purpose_debt": "Debt Payments",
    "grant_purpose_maintenance_indoor": "Indoor Maintenance",
    "grant_purp_cons_outdoor_seating": "Outdoor Seating Construction",
    "grant_purpose_covered_supplier": "Covered Supplier Costs",
}
OWNERSHIP_COLS = {
    "Women-owned": "WomenOwnedIndicator",
    "Veteran-owned": "VeteranIndicator",
    "Socioeconomically disadvantaged": "SocioeconmicIndicator",
}
GROUP_COLS = {
    "Entity Type (Legal Org)": "LegalOrganizationType",
    "Urban vs Rural": "Urban/Rural",
    "Franchise vs Independent": "Franchise",
    "Top 15 Cities": "BusinessCity",
}
TABLE_COLS = [
    "BusinessName", "BusinessCity", "GrantAmount", "RestaurantType",
    "LegalOrganizationType", "Franchise", "Urban/Rural", "HubzoneIndicator",
    "LMIIndicator", "WomenOwnedIndicator", "VeteranIndicator", "SocioeconmicIndicator",
]


def dollars(x, pos=None):
    if abs(x) >= 1e9:
        return f"${x / 1e9:.1f}B"
    if abs(x) >= 1e6:
        return f"${x / 1e6:.1f}M"
    if abs(x) >= 1e3:
        return f"${x / 1e3:.0f}K"
    return f"${x:.0f}"


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


st.title("SBA Restaurant Revitalization Fund - Grant Explorer")
st.write(
    "The Restaurant Revitalization Fund (RRF) gave grants to restaurants and bars hurt by "
    "COVID-19. This app explores **6,077 California grants** to answer three questions: "
    "How large were the grants? Which kinds of businesses received the most money? "
    "And did the funding reach underserved owners and communities? "
    "Use the **Filters** in the left sidebar to focus on any segment. Every number and "
    "chart on this page updates to match."
)


@st.cache_data
def load_data():
    df = pd.read_csv("data/SBA_RRF.csv")
    df["Urban/Rural"] = df["RuralUrbanIndicator"].map({"U": "Urban", "R": "Rural"})
    df["Franchise"] = df["Is_Franchise"].map({1: "Franchise", 0: "Independent"})
    return df


df = load_data()
filtered = df.copy()

st.sidebar.header("Filters")
st.sidebar.caption("Leave a filter empty (or on 'All') to include everything.")

filtered = sidebar_isin(
    filtered, "City", sorted(df["BusinessCity"].dropna().unique()), "BusinessCity"
)

min_grant = int(np.floor(df["GrantAmount"].min()))
max_grant = int(np.ceil(df["GrantAmount"].max()))
grant_range = st.sidebar.slider(
    "Grant Amount ($)", min_grant, max_grant, (min_grant, max_grant), step=5000, format="$%d"
)
filtered = filtered[filtered["GrantAmount"].between(grant_range[0], grant_range[1])]

filtered = sidebar_flags(
    filtered, "Restaurant Type", {t: t for t in RESTAURANT_TYPES},
    help="A business can be more than one type. Rows matching any selected type are kept.",
)
filtered = sidebar_choice(
    filtered, "Urban vs Rural", ["Urban", "Rural"], "Urban/Rural", widget="radio", horizontal=True
)
filtered = sidebar_choice(
    filtered, "HUBZone", ["In HUBZone", "Not in HUBZone"], "HubzoneIndicator",
    mapping={"In HUBZone": 1, "Not in HUBZone": 0},
    help="HUBZones are SBA-designated historically underutilized business zones.",
)
filtered = sidebar_flags(
    filtered, "Ownership Type", OWNERSHIP_COLS,
    help="Rows matching any selected ownership type are kept.",
)
filtered = sidebar_flags(
    filtered, "Grant Purpose", {label: col for col, label in PURPOSE_COLS.items()},
    help="Rows where the recipient listed any selected purpose are kept.",
)

st.sidebar.subheader("Entity Type")
filtered = sidebar_choice(
    filtered, "Franchise or Independent", ["Franchise", "Independent"], "Franchise"
)
filtered = sidebar_isin(
    filtered, "Legal Organization Type",
    df["LegalOrganizationType"].value_counts().index.tolist(), "LegalOrganizationType",
)
if st.sidebar.checkbox(
    "Only low-income (LMI) communities",
    help="Keep only businesses located in low- and moderate-income (LMI) areas.",
):
    filtered = filtered[filtered["LMIIndicator"] == 1]

if filtered.empty:
    st.warning("No grants match the selected filters. Try removing one or more filters.")
    st.stop()

for column, (label, value) in zip(st.columns(4), [
    ("Number of Grants", f"{len(filtered):,}"),
    ("Total Grant Dollars", dollars(filtered["GrantAmount"].sum())),
    ("Median Grant", dollars(filtered["GrantAmount"].median())),
    ("Women-owned Share", f"{filtered['WomenOwnedIndicator'].mean() * 100:.1f}%"),
]):
    column.metric(label, value)
st.caption(f"Showing {len(filtered):,} of {len(df):,} grants based on the current filters.")

st.divider()
st.subheader("1. How large were the grants?")
st.write("Distribution of grant amounts for the selected businesses.")

bins_col, log_col = st.columns(2)
bins = bins_col.slider("Number of Bins", 5, 50, 30)
log_scale = log_col.checkbox(
    "Log scale (x-axis)", value=True,
    help="Grants range from about $1K to $10M. A log scale spreads out the smaller grants.",
)

fig, ax = plt.subplots(figsize=(10, 4))
amounts = filtered["GrantAmount"]
if log_scale and amounts.nunique() > 1:
    ax.hist(amounts, bins=np.logspace(np.log10(amounts.min()), np.log10(amounts.max()), bins + 1),
            color="steelblue", edgecolor="white")
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
st.caption("Each bar counts how many grants fall in that dollar range. The dashed orange line marks the median grant.")

st.divider()
st.subheader("2. Which businesses received the most funding?")
st.write("Compare grant funding across business segments.")

group_col, metric_col = st.columns(2)
group_by = group_col.selectbox("Group by", [
    "Restaurant Type",
    "Entity Type (Legal Org)",
    "Urban vs Rural",
    "Ownership Type",
    "Franchise vs Independent",
    "Top 15 Cities",
])
metric = metric_col.radio(
    "Metric", ["Total Grant $", "Average Grant $", "Number of Grants"], horizontal=True
)

if group_by == "Restaurant Type":
    segment = flag_metric(filtered, {t: t for t in RESTAURANT_TYPES}, metric)
elif group_by == "Ownership Type":
    segment = flag_metric(filtered, OWNERSHIP_COLS, metric)
else:
    grouped = filtered.groupby(GROUP_COLS[group_by])["GrantAmount"]
    segment = grouped.size() if metric == "Number of Grants" else (
        grouped.sum() if metric == "Total Grant $" else grouped.mean()
    )
    if group_by == "Top 15 Cities":
        segment = segment[segment.index.isin(filtered["BusinessCity"].value_counts().head(15).index)]

segment = segment[segment > 0].sort_values(ascending=False)
hbar(
    segment, f"{metric} by {group_by}", metric, group_by, "seagreen",
    kind="count" if metric == "Number of Grants" else "dollars",
)
if group_by in ("Restaurant Type", "Ownership Type"):
    st.caption(
        f"A business can belong to more than one {group_by.lower()}, "
        "so bar totals can add up to more than the overall total."
    )
else:
    st.caption("Longer bars mean more funding for that segment.")

st.divider()
st.subheader("3. How did recipients plan to use the money?")
st.write("Share of selected grants that listed each spending purpose.")

purpose_share = filtered[list(PURPOSE_COLS)].mean() * 100
purpose_share.index = [PURPOSE_COLS[c] for c in purpose_share.index]
if st.checkbox("Sort purposes from most to least common", value=True):
    purpose_share = purpose_share.sort_values(ascending=False)
hbar(purpose_share, "Grant Purpose (% of Grants)", "Percent of Grants", "Grant Purpose", "slateblue", kind="percent")
st.caption("Recipients could select more than one purpose, so percentages do not add up to 100%.")

st.divider()
st.subheader("Summary Statistics")
st.write("Grant amount statistics for the selected businesses.")
st.write(filtered["GrantAmount"].describe())

with st.expander("View filtered data"):
    st.dataframe(
        filtered[TABLE_COLS].sort_values("GrantAmount", ascending=False),
        hide_index=True,
    )
