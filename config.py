from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "SBA_RRF.csv"

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
RESTAURANT_TYPE_COLS = {t: t for t in RESTAURANT_TYPES}

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

# Chart 2 options. Restaurant Type and Ownership Type use yes/no columns; the rest use groupby.
FLAG_GROUPS = {
    "Restaurant Type": RESTAURANT_TYPE_COLS,
    "Ownership Type": OWNERSHIP_COLS,
}
GROUP_COLS = {
    "Entity Type (Legal Org)": "LegalOrganizationType",
    "Urban vs Rural": "Urban/Rural",
    "Franchise vs Independent": "Franchise",
    "Top 15 Cities": "BusinessCity",
    "Top 15 ZIP Codes": "ZIP",
}
GROUP_BY_OPTIONS = [
    "Restaurant Type",
    "Entity Type (Legal Org)",
    "Urban vs Rural",
    "Ownership Type",
    "Franchise vs Independent",
    "Top 15 Cities",
    "Top 15 ZIP Codes",
]
METRICS = ["Total Grant $", "Average Grant $", "Number of Grants"]

# Yes/no columns shown as tags in the map tooltip and grant details card.
TAG_COLS = {
    "Women-owned": "WomenOwnedIndicator",
    "Veteran-owned": "VeteranIndicator",
    "Socioeconomically disadvantaged": "SocioeconmicIndicator",
    "Low-income community": "LMIIndicator",
    "HUBZone": "HubzoneIndicator",
}

MAP_COLORS = {
    "Women-owned": "WomenOwnedIndicator",
    "Low-income (LMI) community": "LMIIndicator",
    "HUBZone": "HubzoneIndicator",
    "Franchise": "Is_Franchise",
}
TABLE_COLS = [
    "BusinessName", "BusinessCity", "ZIP", "GrantAmount", "RestaurantType",
    "LegalOrganizationType", "Franchise", "Urban/Rural", "HubzoneIndicator",
    "LMIIndicator", "WomenOwnedIndicator", "VeteranIndicator", "SocioeconmicIndicator",
]
