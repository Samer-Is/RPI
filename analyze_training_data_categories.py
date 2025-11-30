"""
Analyze the training data to get the last prices per category
"""
import pandas as pd

# Read the training data
df = pd.read_parquet('data/processed/training_data.parquet')

print("Training Data Overview:")
print("="*70)
print(f"Total rows: {len(df)}")
print(f"\nColumns ({len(df.columns)}): {df.columns.tolist()}")
print(f"\nFirst few rows:")
print(df.head())

# Check if we have category and pricing information
if 'category' in df.columns and 'daily_rate' in df.columns:
    print("\n" + "="*70)
    print("Latest Rental Price per Category:")
    print("="*70)
    
    # Get the last (most recent) price for each category
    df_sorted = df.sort_values('date')
    latest_prices = df_sorted.groupby('category').tail(1)[[' category', 'date', 'daily_rate']]
    
    print(latest_prices.to_string(index=False))
    
    print("\n" + "="*70)
    print("Average of Last 10 Rentals per Category:")
    print("="*70)
    
    last_10_avg = df_sorted.groupby('category').tail(10).groupby('category')['daily_rate'].mean()
    for cat, avg in last_10_avg.items():
        print(f"{cat:20} {avg:8.2f} SAR/day")
    
else:
    print("\nError: category or daily_rate columns not found")
    print(f"Available columns: {df.columns.tolist()}")

