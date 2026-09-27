# SBA Restaurant Revitalization Fund - Grant Explorer

An interactive Streamlit app for exploring how the SBA Restaurant Revitalization Fund (RRF) distributed grant dollars to California restaurants.

## Business Problem

The RRF gave grants to restaurants, bars, and other food and beverage businesses hurt by COVID-19. Policy makers, lenders, and restaurant associations want to know:

**How were RRF grant dollars spread across California restaurants, and did they reach underserved businesses** (women-owned, veteran-owned, socioeconomically disadvantaged, businesses in low-income communities, HUBZones, and rural areas)?

The app answers four business questions:

1. **How large were the grants?** Distribution of grant amounts for any segment.
2. **Which businesses received the most funding?** Total, average, or count of grants by restaurant type, entity type, ownership, urban vs rural, franchise status, city, or ZIP code.
3. **How did recipients plan to use the money?** Share of grants listing each of 10 spending purposes (payroll, rent, utilities, and so on).
4. **Where did the money go?** A map of every grant, plus a city profile that breaks funding down by ZIP code.

## Dataset

- File: `data/SBA_RRF.csv` (6,077 grants, 50 columns, all in California, about $2.34B total)
- Source: SBA Restaurant Revitalization Fund public award data, provided as `SBA_RRF.xlsx`
- `convert_data.py` converts the original Excel file to the CSV the app reads:

```bash
python convert_data.py path/to/SBA_RRF.xlsx
```

Key columns:

| Column(s) | Meaning |
| --- | --- |
| `BusinessCity`, `BusinessZip` | City and ZIP code of the business |
| `Latitude`, `Longitude` | Business location, used for the map |
| `GrantAmount` | Grant amount in dollars |
| `Bakery` ... `Winery` | 13 yes/no (1/0) restaurant type flags; a business can have several |
| `RuralUrbanIndicator` | `U` = Urban, `R` = Rural |
| `HubzoneIndicator` | 1 = located in an SBA HUBZone |
| `WomenOwnedIndicator`, `VeteranIndicator`, `SocioeconmicIndicator` | Ownership flags (the last one is misspelled in the source data) |
| `grant_purpose_*` | 10 yes/no flags for how the grant would be used |
| `Is_Franchise`, `LegalOrganizationType` | Entity type |
| `LMIIndicator` | 1 = located in a low- or moderate-income community |

## App Features

**Sidebar filters** (every chart and number updates to match):

- City
- ZIP Code (lists only ZIP codes in the selected cities)
- Grant Amount range
- Restaurant Type
- Urban vs Rural
- HUBZone
- Ownership Type (women-owned, veteran-owned, socioeconomically disadvantaged)
- Grant Purpose
- Entity Type (franchise vs independent, legal organization type)
- Low Income Community

**Outputs:**

- Headline metrics: number of grants, total dollars, median grant, women-owned share
- Chart 1: Histogram of grant amounts, with a bins slider and log-scale checkbox
- Chart 2: Bar chart of grant funding by segment, with group-by and metric controls
- Chart 3: Bar chart of grant purposes
- Chart 4: Map of grants, sized by grant amount, with an option to highlight women-owned, low-income, HUBZone, or franchise grants
- City profile: pick a city to see its headline numbers, a map, and a ZIP code breakdown
- Summary statistics and a table of the filtered grants

## How to Run

1. Clone this repository and move into the folder:

```bash
git clone https://github.com/asarje-csueb/data-analysis-project.git
cd data-analysis-project
```

2. (Optional) Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install the required libraries:

```bash
pip install -r requirements.txt
```

4. Launch the app:

```bash
python -m streamlit run app.py
```

The app opens at http://localhost:8501.

## Tools Used

- **Python**: core application logic
- **Streamlit**: web interface and interactive controls
- **Pandas / NumPy**: data loading and filtering
- **Matplotlib / Seaborn**: charts

## Repository Structure

```
data-analysis-project/
├── app.py              # Entry point: page setup and main() that runs each section in order
├── config.py           # Column lists and business-friendly labels
├── data_loader.py      # Loads and caches the CSV, adds readable columns
├── filters.py          # Sidebar filters
├── charts.py           # Reusable chart, map, and formatting helpers
├── sections.py         # One function per page section (KPIs, charts 1-4, city profile, summary)
├── convert_data.py     # One-time Excel to CSV conversion
├── data/
│   └── SBA_RRF.csv     # RRF grant data
├── requirements.txt
└── README.md
```
