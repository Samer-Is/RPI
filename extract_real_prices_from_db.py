"""
Extract REAL Prices from Database - NO HARD-CODING
This script extracts actual contract prices from the database to replace hard-coded values
"""

from db import DatabaseConnection
import pandas as pd
import numpy as np
from datetime import datetime
import json

print("="*100)
print("EXTRACTING REAL PRICES FROM DATABASE - NO SIMULATIONS")
print("="*100)
print(f"Extraction Time: {datetime.now()}")
print("="*100)

with DatabaseConnection() as db:
    
    # ========================================================================
    # QUERY 1: Overall Price Statistics
    # ========================================================================
    print("\n[STEP 1] OVERALL CONTRACT PRICE STATISTICS")
    print("-"*100)
    
    query1 = """
    SELECT 
        COUNT(*) as TotalContracts,
        AVG(DailyRateAmount) as AvgPrice,
        MIN(DailyRateAmount) as MinPrice,
        MAX(DailyRateAmount) as MaxPrice,
        STDEV(DailyRateAmount) as StdDevPrice
    FROM [Rental].[Contract]
    WHERE Start >= '2023-01-01'
        AND DailyRateAmount IS NOT NULL
        AND DailyRateAmount BETWEEN 50 AND 2000
    """
    
    result1 = db.execute_query(query1)
    print(result1.to_string(index=False))
    
    total_contracts = result1['TotalContracts'].iloc[0]
    avg_price = result1['AvgPrice'].iloc[0]
    
    print(f"\nTotal Contracts Analyzed: {total_contracts:,}")
    print(f"Average Daily Rate: {avg_price:.2f} SAR")
    
    # ========================================================================
    # QUERY 2: Price by Branch (Top Branches)
    # ========================================================================
    print("\n\n[STEP 2] AVERAGE PRICES BY BRANCH")
    print("-"*100)
    
    query2 = """
    SELECT TOP 20
        c.PickupBranchId,
        b.Name as BranchName,
        CASE WHEN b.IsAirport = 1 THEN 'Airport' ELSE 'City' END as LocationType,
        COUNT(*) as Contracts,
        ROUND(AVG(c.DailyRateAmount), 0) as AvgPrice,
        ROUND(MIN(c.DailyRateAmount), 0) as MinPrice,
        ROUND(MAX(c.DailyRateAmount), 0) as MaxPrice,
        ROUND(STDEV(c.DailyRateAmount), 0) as StdDev
    FROM [Rental].[Contract] c
    LEFT JOIN [Rental].[Branches] b ON c.PickupBranchId = b.Id
    WHERE c.Start >= '2024-01-01'
        AND c.DailyRateAmount IS NOT NULL
        AND c.DailyRateAmount BETWEEN 50 AND 2000
    GROUP BY c.PickupBranchId, b.Name, b.IsAirport
    HAVING COUNT(*) >= 100
    ORDER BY Contracts DESC
    """
    
    df_branches = db.execute_query(query2)
    # Save to file to avoid unicode issues
    df_branches.to_csv('data/branch_prices.csv', index=False)
    print(f"Branch prices saved to data/branch_prices.csv ({len(df_branches)} branches)")
    print(f"Sample (first 5):")
    print(df_branches.head()[['PickupBranchId', 'LocationType', 'Contracts', 'AvgPrice']].to_string(index=False))
    
    # Calculate airport premium
    airport_prices = df_branches[df_branches['LocationType'] == 'Airport']['AvgPrice']
    city_prices = df_branches[df_branches['LocationType'] == 'City']['AvgPrice']
    
    if len(airport_prices) > 0 and len(city_prices) > 0:
        airport_premium = (airport_prices.mean() / city_prices.mean() - 1) * 100
        print(f"\nAirport Premium (actual data): {airport_premium:+.1f}%")
    
    # ========================================================================
    # QUERY 3: Check if we can identify vehicle categories
    # ========================================================================
    print("\n\n[STEP 3] CHECKING VEHICLE CATEGORY DATA")
    print("-"*100)
    
    # First, check if Models table has category info
    query3_check = """
    SELECT TOP 5 COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'Fleet'
        AND TABLE_NAME = 'Models'
        AND (COLUMN_NAME LIKE '%Category%' OR COLUMN_NAME LIKE '%Type%' OR COLUMN_NAME LIKE '%Class%')
    """
    
    category_columns = db.execute_query(query3_check)
    print("Category-related columns in Fleet.Models:")
    if len(category_columns) > 0:
        for col in category_columns['COLUMN_NAME']:
            print(f"  - {col}")
    else:
        print("  No obvious category columns found")
    
    # Try to get model data
    query3 = """
    SELECT TOP 100
        m.Id as ModelId,
        m.Name as ModelName,
        m.MakeId,
        COUNT(DISTINCT c.Id) as ContractCount,
        ROUND(AVG(c.DailyRateAmount), 0) as AvgPrice
    FROM [Fleet].[Models] m
    INNER JOIN [Fleet].[Vehicles] v ON m.Id = v.ModelId
    INNER JOIN [Rental].[Contract] c ON v.Id = c.VehicleId
    WHERE c.Start >= '2024-01-01'
        AND c.DailyRateAmount BETWEEN 50 AND 2000
        AND c.DailyRateAmount IS NOT NULL
    GROUP BY m.Id, m.Name, m.MakeId
    HAVING COUNT(DISTINCT c.Id) >= 10
    ORDER BY ContractCount DESC
    """
    
    df_models = db.execute_query(query3)
    df_models.to_csv('data/model_prices.csv', index=False)
    print(f"\nModel prices saved to data/model_prices.csv ({len(df_models)} models)")
    print(f"Sample (first 5):")
    print(df_models.head()[['ModelId', 'ContractCount', 'AvgPrice']].to_string(index=False))
    
    # ========================================================================
    # QUERY 4: Weekend vs Weekday Pricing
    # ========================================================================
    print("\n\n[STEP 4] WEEKEND VS WEEKDAY PRICING")
    print("-"*100)
    
    query4 = """
    SELECT 
        CASE 
            WHEN DATEPART(weekday, Start) IN (5, 6) THEN 'Weekend'
            ELSE 'Weekday'
        END as DayType,
        COUNT(*) as Contracts,
        ROUND(AVG(DailyRateAmount), 0) as AvgPrice,
        ROUND(STDEV(DailyRateAmount), 0) as StdDev
    FROM [Rental].[Contract]
    WHERE Start >= '2024-01-01'
        AND DailyRateAmount BETWEEN 50 AND 2000
        AND DailyRateAmount IS NOT NULL
    GROUP BY CASE 
            WHEN DATEPART(weekday, Start) IN (5, 6) THEN 'Weekend'
            ELSE 'Weekday'
        END
    """
    
    df_weekend = db.execute_query(query4)
    print(df_weekend.to_string(index=False))
    
    if len(df_weekend) == 2:
        weekend_price = df_weekend[df_weekend['DayType'] == 'Weekend']['AvgPrice'].iloc[0]
        weekday_price = df_weekend[df_weekend['DayType'] == 'Weekday']['AvgPrice'].iloc[0]
        weekend_premium = (weekend_price / weekday_price - 1) * 100
        print(f"\nWeekend Premium (actual data): {weekend_premium:+.1f}%")
    
    # ========================================================================
    # QUERY 5: Price Distribution (Percentiles)
    # ========================================================================
    print("\n\n[STEP 5] PRICE DISTRIBUTION ANALYSIS")
    print("-"*100)
    
    query5 = """
    SELECT 
        DailyRateAmount
    FROM [Rental].[Contract]
    WHERE Start >= '2023-01-01'
        AND DailyRateAmount BETWEEN 50 AND 2000
        AND DailyRateAmount IS NOT NULL
    """
    
    df_prices = db.execute_query(query5)
    
    print(f"Total Contracts: {len(df_prices):,}")
    print(f"\nPrice Percentiles:")
    print(f"  10th Percentile: {df_prices['DailyRateAmount'].quantile(0.10):.0f} SAR")
    print(f"  25th Percentile: {df_prices['DailyRateAmount'].quantile(0.25):.0f} SAR")
    print(f"  50th Percentile (Median): {df_prices['DailyRateAmount'].quantile(0.50):.0f} SAR")
    print(f"  75th Percentile: {df_prices['DailyRateAmount'].quantile(0.75):.0f} SAR")
    print(f"  90th Percentile: {df_prices['DailyRateAmount'].quantile(0.90):.0f} SAR")
    
    # ========================================================================
    # GENERATE RECOMMENDATION
    # ========================================================================
    print("\n\n" + "="*100)
    print("RECOMMENDED BASE PRICES (from actual database)")
    print("="*100)
    
    median_price = df_prices['DailyRateAmount'].quantile(0.50)
    p25_price = df_prices['DailyRateAmount'].quantile(0.25)
    p75_price = df_prices['DailyRateAmount'].quantile(0.75)
    
    # Estimate category prices based on distribution
    # Assuming categories are spread across price ranges
    print("\nBased on price distribution:")
    print(f"  Lower-End (Economy-Compact):  ~{p25_price:.0f} SAR")
    print(f"  Mid-Range (Standard-SUV):     ~{median_price:.0f} SAR")
    print(f"  Upper-End (Luxury):           ~{p75_price:.0f} SAR")
    
    print("\nCurrent Hard-Coded vs Database Median:")
    print("-"*100)
    
    hard_coded = {
        'Economy': 150,
        'Compact': 180,
        'Standard': 220,
        'SUV Compact': 280,
        'SUV Standard': 350,
        'SUV Large': 500,
        'Luxury Sedan': 600,
        'Luxury SUV': 800
    }
    
    for category, hc_price in hard_coded.items():
        diff = median_price - hc_price
        pct_diff = (diff / hc_price) * 100
        status = "OK" if abs(pct_diff) < 10 else ("TOO LOW" if diff > 0 else "TOO HIGH")
        print(f"  {category:15s}: {hc_price:4.0f} SAR (Hard-coded) vs {median_price:.0f} SAR (DB Median) = {pct_diff:+6.1f}% [{status}]")
    
    # Save results to JSON
    results = {
        'extraction_date': datetime.now().isoformat(),
        'total_contracts': int(total_contracts),
        'overall_stats': {
            'mean': float(avg_price),
            'median': float(median_price),
            'p25': float(p25_price),
            'p75': float(p75_price),
        },
        'branch_prices': df_branches.to_dict('records'),
        'model_prices': df_models.to_dict('records'),
        'weekend_analysis': df_weekend.to_dict('records'),
    }
    
    with open('data/real_prices_from_database.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n" + "="*100)
    print("RESULTS SAVED: data/real_prices_from_database.json")
    print("="*100)
    
print("\n[EXTRACTION COMPLETE]")

