import pandas as pd

# Load the daily city-level data
df = pd.read_csv('../data/city_day.csv')

# Filter for Delhi only
delhi_data = df[df['City'] == 'Delhi']

# Basic info
print("Total Delhi records:", len(delhi_data))
print("\nDate range:", delhi_data['Date'].min(), "to", delhi_data['Date'].max())
print("\nColumns available:", list(delhi_data.columns))
print("\nFirst 5 rows:")
print(delhi_data.head())

# Check for missing AQI values
print("\nMissing AQI values:", delhi_data['AQI'].isna().sum())

# Save cleaned Delhi-only data for later use
delhi_data.to_csv('../data/delhi_aqi_clean.csv', index=False)
print("\nSaved delhi_aqi_clean.csv")
