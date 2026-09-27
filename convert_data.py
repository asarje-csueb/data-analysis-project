import sys

import pandas as pd

source = sys.argv[1] if len(sys.argv) > 1 else "SBA_RRF.xlsx"

df = pd.read_excel(source)
df.to_csv("data/SBA_RRF.csv", index=False)

print(f"Wrote data/SBA_RRF.csv with {len(df):,} rows and {df.shape[1]} columns")
