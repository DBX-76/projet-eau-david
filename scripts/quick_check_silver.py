import pandas as pd
import os
from datetime import datetime

silver_file = "./data/clean/silver_clean.csv"

# Get file info
stat = os.stat(silver_file)
print(f"File size: {stat.st_size / 1024 / 1024:.2f} MB")
print(f"Last modified: {datetime.fromtimestamp(stat.st_mtime)}")

# Read a small sample
print("\nReading first 10 rows...")
df = pd.read_csv(silver_file, sep=';', encoding='iso-8859-1', nrows=10)

print(f"\nColumns: {df.columns.tolist()}")
print(f"\nShape: {df.shape}")

# Check for communes
if 'nom_commune' in df.columns:
    print(f"\nnom_commune non-nulls in sample: {df['nom_commune'].notna().sum()}/{len(df)}")
    print(f"Unique communes in sample: {df['nom_commune'].nunique()}")
    print(f"Sample communes: {df['nom_commune'].dropna().unique()[:3]}")

# Check for dates
if 'date_prelevement' in df.columns:
    print(f"\ndate_prelevement non-nulls in sample: {df['date_prelevement'].notna().sum()}/{len(df)}")
    print(f"Sample dates: {df['date_prelevement'].dropna().unique()[:3]}")

print("\n✅ Quick check complete!")
