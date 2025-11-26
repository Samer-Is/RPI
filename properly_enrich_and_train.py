"""
PROPER DATA ENRICHMENT AND MODEL TRAINING
Fixes the missing features issue
"""
import pandas as pd
import numpy as np
from datetime import datetime
from external_data_fetcher import create_holiday_features
import warnings
warnings.filterwarnings('ignore')

print("="*100)
print("PROPER DATA ENRICHMENT - FIXING MISSING FEATURES")
print("="*100)

# Load base enriched data
print("\n[1] Loading base enriched data...")
df = pd.read_parquet('data/processed/training_data_enriched.parquet')
print(f"Loaded: {len(df):,} rows, {len(df.columns)} columns")

# Add external/holiday features
print("\n[2] Adding external holiday/event features...")
df['Date'] = pd.to_datetime(df['Start']).dt.date
df['Date'] = pd.to_datetime(df['Date'])

# Get date range
start_date = df['Date'].min()
end_date = df['Date'].max()
print(f"Date range: {start_date} to {end_date}")

# Create holiday features for date range
df_holidays = create_holiday_features(start_date=start_date, end_date=end_date)
print(f"Holiday features created: {len(df_holidays)} dates, {len(df_holidays.columns)} columns")

# Merge with main data
df = df.merge(df_holidays, left_on='Date', right_on='date', how='left')
print(f"After merge: {len(df.columns)} columns")

# Check what we got
external_cols = [c for c in df.columns if 'holiday' in c.lower() or 'ramadan' in c.lower() or 'hajj' in c.lower() or 'umrah' in c.lower() or 'festival' in c.lower() or 'sports' in c.lower() or 'vacation' in c.lower()]
print(f"External features added: {len(external_cols)}")
for col in external_cols:
    print(f"  - {col}: {df[col].sum() if df[col].dtype in [int, bool] else 'N/A'}")

# Add temporal features
print("\n[3] Adding temporal features...")
df['day_of_week'] = df['Date'].dt.dayofweek
df['DayOfMonth'] = df['Date'].dt.day
df['WeekOfYear'] = df['Date'].dt.isocalendar().week.astype(int)
df['month'] = df['Date'].dt.month
df['quarter'] = df['Date'].dt.quarter
df['is_weekend'] = df['day_of_week'].isin([4, 5]).astype(int)
df['DayOfYear'] = df['Date'].dt.dayofyear

print(f"Temporal features added: 7")

# Add Fourier features
print("\n[4] Adding Fourier features...")
# Yearly seasonality
df['sin_365_1'] = np.sin(2 * np.pi * df['DayOfYear'] / 365)
df['cos_365_1'] = np.cos(2 * np.pi * df['DayOfYear'] / 365)
df['sin_365_2'] = np.sin(4 * np.pi * df['DayOfYear'] / 365)
df['cos_365_2'] = np.cos(4 * np.pi * df['DayOfYear'] / 365)

# Weekly seasonality
df['sin_7_1'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
df['cos_7_1'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
df['sin_7_2'] = np.sin(4 * np.pi * df['day_of_week'] / 7)
df['cos_7_2'] = np.cos(4 * np.pi * df['day_of_week'] / 7)

print(f"Fourier features added: 8")

# Add aggregation features
print("\n[5] Adding aggregation features...")
df['BranchHistoricalSize'] = df.groupby('PickupBranchId')['Id'].transform('count')
df['IsAirportBranch'] = df['IsAirport'].astype(int)
df['CitySize'] = df.groupby('CityId')['Id'].transform('count')
df['BranchAvgPrice'] = df.groupby('PickupBranchId')['DailyRateAmount'].transform('mean')
df['CityAvgPrice'] = df.groupby('CityId')['DailyRateAmount'].transform('mean')
df['FleetSize'] = df.groupby(['Date', 'PickupBranchId']).size()
df['CapacityIndicator'] = df['BranchHistoricalSize'] / df['CitySize']

print(f"Aggregation features added: 7")

# Add enhanced holiday features if we have the basic ones
if 'is_holiday' in df.columns and 'holiday_duration' in df.columns:
    print("\n[6] Adding enhanced holiday features...")
    df['is_long_holiday'] = (df['holiday_duration'] >= 4).astype(int)
    df['near_holiday'] = ((df['days_to_holiday'] >= 0) & (df['days_to_holiday'] <= 2)).astype(int)
    df['post_holiday'] = ((df['days_from_holiday'] >= 0) & (df['days_from_holiday'] <= 2)).astype(int)
    print(f"Enhanced holiday features added: 3")
else:
    print("\n[WARNING] Basic holiday features not found - cannot create enhanced features")

# Summary
print("\n" + "="*100)
print("ENRICHMENT COMPLETE")
print("="*100)
print(f"Total columns: {len(df.columns)}")
print(f"Total rows: {len(df):,}")

# Save properly enriched data
output_file = 'data/processed/training_data_PROPERLY_enriched.parquet'
df.to_parquet(output_file)
print(f"\nSaved to: {output_file}")

# Verify against model requirements
import pickle
model = pickle.load(open('models/demand_prediction_model_v3_final.pkl', 'rb'))
model_features = set(model.feature_names_in_)
data_features = set(df.columns)
still_missing = model_features - data_features

print(f"\n[VERIFICATION] Features still missing: {len(still_missing)}")
if still_missing:
    print("Missing features:")
    for f in sorted(still_missing):
        print(f"  - {f}")
else:
    print("[OK] All model features are now present in data!")

print("\n" + "="*100)

