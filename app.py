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

# "Socioeconmic" is misspelled in the source data.
OWNERSHIP_COLS = {
    "Women-owned": "WomenOwnedIndicator",
    "Veteran-owned": "VeteranIndicator",
    "Socioeconomically disadvantaged": "SocioeconmicIndicator",
}


def dollars(x, pos=None):
    if abs(x) >= 1e9:
        return f"${x / 1e9:.1f}B"
    if abs(x) >= 1e6:
        return f"${x / 1e6:.1f}M"
    if abs(x) >= 1e3:
        return f"${x / 1e3:.0f}K"
    return f"${x:.0f}"


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

# 1. City
cities = st.sidebar.multiselect(
    "City",
    sorted(df["BusinessCity"].dropna().unique()),
)
if cities:
    filtered = filtered[filtered["BusinessCity"].isin(cities)]

# 2. Grant Amount
min_grant = int(np.floor(df["GrantAmount"].min()))
max_grant = int(np.ceil(df["GrantAmount"].max()))
grant_range = st.sidebar.slider(
    "Grant Amount ($)",
    min_grant,
    max_grant,
    (min_grant, max_grant),
    step=5000,
    format="$%d",
)
filtered = filtered[filtered["GrantAmount"].between(grant_range[0], grant_range[1])]

# 3. Restaurant Type
restaurant_types = st.sidebar.multiselect(
    "Restaurant Type",
    RESTAURANT_TYPES,
    help="A business can be more than one type. Rows matching any selected type are kept.",
)
if restaurant_types:
    filtered = filtered[filtered[restaurant_types].eq(1).any(axis=1)]

# 4. Urban vs Rural
urban_rural = st.sidebar.radio(
    "Urban vs Rural",
    ["All", "Urban", "Rural"],
    horizontal=True,
)
if urban_rural != "All":
    filtered = filtered[filtered["Urban/Rural"] == urban_rural]

# 5. Hubzone
hubzone = st.sidebar.selectbox(
    "HUBZone",
    ["All", "In HUBZone", "Not in HUBZone"],
    help="HUBZones are SBA-designated historically underutilized business zones.",
)
if hubzone != "All":
    filtered = filtered[filtered["HubzoneIndicator"] == (1 if hubzone == "In HUBZone" else 0)]

# 6. Ownership Type
ownership = st.sidebar.multiselect(
    "Ownership Type",
    list(OWNERSHIP_COLS.keys()),
    help="Rows matching any selected ownership type are kept.",
)
if ownership:
    ownership_cols = [OWNERSHIP_COLS[o] for o in ownership]
    filtered = filtered[filtered[ownership_cols].eq(1).any(axis=1)]

# 7. Grant Purpose
purpose_labels = {label: col for col, label in PURPOSE_COLS.items()}
purposes = st.sidebar.multiselect(
    "Grant Purpose",
    list(purpose_labels.keys()),
    help="Rows where the recipient listed any selected purpose are kept.",
)
if purposes:
    purpose_cols = [purpose_labels[p] for p in purposes]
    filtered = filtered[filtered[purpose_cols].eq(1).any(axis=1)]

# 8. Entity Type
st.sidebar.subheader("Entity Type")
franchise = st.sidebar.selectbox(
    "Franchise or Independent",
    ["All", "Franchise", "Independent"],
)
if franchise != "All":
    filtered = filtered[filtered["Franchise"] == franchise]

legal_types = st.sidebar.multiselect(
    "Legal Organization Type",
    df["LegalOrganizationType"].value_counts().index.tolist(),
)
if legal_types:
    filtered = filtered[filtered["LegalOrganizationType"].isin(legal_types)]

# 9. Low Income Community
low_income = st.sidebar.checkbox(
    "Only low-income (LMI) communities",
    help="Keep only businesses located in low- and moderate-income (LMI) areas.",
)
if low_income:
    filtered = filtered[filtered["LMIIndicator"] == 1]

if filtered.empty:
    st.warning("No grants match the selected filters. Try removing one or more filters.")
    st.stop()

# KPI row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Number of Grants", f"{len(filtered):,}")
col2.metric("Total Grant Dollars", dollars(filtered["GrantAmount"].sum()))
col3.metric("Median Grant", dollars(filtered["GrantAmount"].median()))
col4.metric("Women-owned Share", f"{filtered['WomenOwnedIndicator'].mean() * 100:.1f}%")
st.caption(f"Showing {len(filtered):,} of {len(df):,} grants based on the current filters.")

st.divider()

# Chart 1: Grant size distribution
st.subheader("1. How large were the grants?")
st.write("Distribution of grant amounts for the selected businesses.")

chart1_col1, chart1_col2 = st.columns(2)
bins = chart1_col1.slider(
    "Number of Bins",
    5,
    50,
    30,
)
log_scale = chart1_col2.checkbox(
    "Log scale (x-axis)",
    value=True,
    help="Grants range from about $1K to $10M. A log scale spreads out the smaller grants.",
)

fig, ax = plt.subplots(figsize=(10, 4))
if log_scale and filtered["GrantAmount"].nunique() > 1:
    hist_bins = np.logspace(
        np.log10(filtered["GrantAmount"].min()),
        np.log10(filtered["GrantAmount"].max()),
        bins + 1,
    )
    ax.hist(filtered["GrantAmount"], bins=hist_bins, color="steelblue", edgecolor="white")
    ax.set_xscale("log")
else:
    ax.hist(filtered["GrantAmount"], bins=bins, color="steelblue", edgecolor="white")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(dollars))
ax.axvline(filtered["GrantAmount"].median(), color="darkorange", linestyle="--", label="Median")
ax.set_title("Distribution of Grant Amount")
ax.set_xlabel("Grant Amount")
ax.set_ylabel("Number of Grants")
ax.legend()
st.pyplot(fig)
st.caption(
    "Each bar counts how many grants fall in that dollar range. "
    "The dashed orange line marks the median grant."
)

st.divider()

# Chart 2: Grant dollars by segment
st.subheader("2. Which businesses received the most funding?")
st.write("Compare grant funding across business segments.")

chart2_col1, chart2_col2 = st.columns(2)
group_by = chart2_col1.selectbox(
    "Group by",
    [
        "Restaurant Type",
        "Entity Type (Legal Org)",
        "Urban vs Rural",
        "Ownership Type",
        "Franchise vs Independent",
        "Top 15 Cities",
    ],
)
metric = chart2_col2.radio(
    "Metric",
    ["Total Grant $", "Average Grant $", "Number of Grants"],
    horizontal=True,
)


def summarize(grants):
    if metric == "Total Grant $":
        return grants.sum()
    if metric == "Average Grant $":
        return grants.mean() if len(grants) else 0
    return len(grants)


if group_by in ("Restaurant Type", "Ownership Type"):
    flag_cols = (
        {t: t for t in RESTAURANT_TYPES} if group_by == "Restaurant Type" else OWNERSHIP_COLS
    )
    segment = pd.Series(
        {
            label: summarize(filtered.loc[filtered[col] == 1, "GrantAmount"])
            for label, col in flag_cols.items()
        }
    )
else:
    group_col = {
        "Entity Type (Legal Org)": "LegalOrganizationType",
        "Urban vs Rural": "Urban/Rural",
        "Franchise vs Independent": "Franchise",
        "Top 15 Cities": "BusinessCity",
    }[group_by]
    grouped = filtered.groupby(group_col)["GrantAmount"]
    if metric == "Total Grant $":
        segment = grouped.sum()
    elif metric == "Average Grant $":
        segment = grouped.mean()
    else:
        segment = grouped.size()
    if group_by == "Top 15 Cities":
        top_cities = filtered["BusinessCity"].value_counts().head(15).index
        segment = segment[segment.index.isin(top_cities)]

segment = segment[segment > 0].sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(10, max(3, 0.45 * len(segment))))
sns.barplot(x=segment.values, y=segment.index, color="seagreen", ax=ax)
if metric == "Number of Grants":
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
else:
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(dollars))
ax.set_title(f"{metric} by {group_by}")
ax.set_xlabel(metric)
ax.set_ylabel(group_by)
st.pyplot(fig)
if group_by in ("Restaurant Type", "Ownership Type"):
    st.caption(
        f"A business can belong to more than one {group_by.lower()}, "
        "so bar totals can add up to more than the overall total."
    )
else:
    st.caption("Longer bars mean more funding for that segment.")

st.divider()

# Chart 3: Grant purpose
st.subheader("3. How did recipients plan to use the money?")
st.write("Share of selected grants that listed each spending purpose.")

sort_purposes = st.checkbox("Sort purposes from most to least common", value=True)

purpose_share = filtered[list(PURPOSE_COLS.keys())].mean() * 100
purpose_share.index = [PURPOSE_COLS[c] for c in purpose_share.index]
if sort_purposes:
    purpose_share = purpose_share.sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(10, 4.5))
sns.barplot(x=purpose_share.values, y=purpose_share.index, color="slateblue", ax=ax)
ax.set_xlim(0, 100)
ax.xaxis.set_major_formatter(mticker.PercentFormatter())
for i, value in enumerate(purpose_share.values):
    ax.text(value + 1, i, f"{value:.0f}%", va="center")
ax.set_title("Grant Purpose (% of Grants)")
ax.set_xlabel("Percent of Grants")
ax.set_ylabel("Grant Purpose")
st.pyplot(fig)
st.caption(
    "Recipients could select more than one purpose, so percentages do not add up to 100%."
)

st.divider()

st.subheader("Summary Statistics")
st.write("Grant amount statistics for the selected businesses.")
st.write(filtered["GrantAmount"].describe())

with st.expander("View filtered data"):
    st.dataframe(
        filtered[
            [
                "BusinessName",
                "BusinessCity",
                "GrantAmount",
                "RestaurantType",
                "LegalOrganizationType",
                "Franchise",
                "Urban/Rural",
                "HubzoneIndicator",
                "LMIIndicator",
                "WomenOwnedIndicator",
                "VeteranIndicator",
                "SocioeconmicIndicator",
            ]
        ].sort_values("GrantAmount", ascending=False),
        hide_index=True,
    )
