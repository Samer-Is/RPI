"""
Extract REAL Prices from Database - SIMPLIFIED VERSION
This version focuses on what we CAN extract successfully
"""

from db import DatabaseConnection
import pandas as pd
import numpy as np
from datetime import datetime
import json

print("="*100)
print("EXTRACTING REAL PRICES FROM DATABASE")
print("="*100)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)

try:
    with DatabaseConnection() as db:
        
        # ================================================================
        # STEP 1: Overall Statistics
        # ================================================================
        print("\n[1] OVERALL PRICE STATISTICS (All Contracts)")
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
        total_contracts = int(result1['TotalContracts'].iloc[0])
        avg_price = float(result1['AvgPrice'].iloc[0])
        
        print(f"Total Contracts:   {total_contracts:,}")
        print(f"Average Price:     {avg_price:.2f} SAR")
        print(f"Min Price:         {result1['MinPrice'].iloc[0]:.0f} SAR")
        print(f"Max Price:         {result1['MaxPrice'].iloc[0]:.0f} SAR")
        print(f"Std Deviation:     {result1['StdDevPrice'].iloc[0]:.2f} SAR")
        
        # ================================================================
        # STEP 2: Price Distribution (Percentiles)
        # ================================================================
        print("\n[2] PRICE DISTRIBUTION (Percentiles)")
        print("-"*100)
        
        query2 = """
        SELECT DailyRateAmount
        FROM [Rental].[Contract]
        WHERE Start >= '2023-01-01'
            AND DailyRateAmount BETWEEN 50 AND 2000
            AND DailyRateAmount IS NOT NULL
        """
        
        df_prices = db.execute_query(query2)
        
        p10 = df_prices['DailyRateAmount'].quantile(0.10)
        p25 = df_prices['DailyRateAmount'].quantile(0.25)
        p50 = df_prices['DailyRateAmount'].quantile(0.50)
        p75 = df_prices['DailyRateAmount'].quantile(0.75)
        p90 = df_prices['DailyRateAmount'].quantile(0.90)
        
        print(f"10th Percentile:   {p10:.0f} SAR")
        print(f"25th Percentile:   {p25:.0f} SAR")
        print(f"50th (Median):     {p50:.0f} SAR")
        print(f"75th Percentile:   {p75:.0f} SAR")
        print(f"90th Percentile:   {p90:.0f} SAR")
        
        # ================================================================
        # STEP 3: Weekend vs Weekday
        # ================================================================
        print("\n[3] WEEKEND VS WEEKDAY PRICING")
        print("-"*100)
        
        query3 = """
        SELECT 
            CASE 
                WHEN DATEPART(weekday, Start) IN (5, 6) THEN 'Weekend'
                ELSE 'Weekday'
            END as DayType,
            COUNT(*) as Contracts,
            ROUND(AVG(DailyRateAmount), 2) as AvgPrice
        FROM [Rental].[Contract]
        WHERE Start >= '2024-01-01'
            AND DailyRateAmount BETWEEN 50 AND 2000
            AND DailyRateAmount IS NOT NULL
        GROUP BY CASE 
                WHEN DATEPART(weekday, Start) IN (5, 6) THEN 'Weekend'
                ELSE 'Weekday'
            END
        """
        
        df_weekend = db.execute_query(query3)
        
        for _, row in df_weekend.iterrows():
            print(f"{row['DayType']:10s}: {row['Contracts']:,} contracts, Avg: {row['AvgPrice']:.2f} SAR")
        
        if len(df_weekend) == 2:
            weekend_avg = df_weekend[df_weekend['DayType'] == 'Weekend']['AvgPrice'].iloc[0]
            weekday_avg = df_weekend[df_weekend['DayType'] == 'Weekday']['AvgPrice'].iloc[0]
            weekend_premium = (weekend_avg / weekday_avg - 1) * 100
            print(f"\nWeekend Premium:   {weekend_premium:+.1f}%")
        
        # ================================================================
        # STEP 4: By Branch (Already saved in previous run)
        # ================================================================
        print("\n[4] BRANCH-LEVEL PRICING")
        print("-"*100)
        
        df_branches = pd.read_csv('data/branch_prices.csv')
        print(f"Loaded {len(df_branches)} branches from previous extraction")
        
        airport_branches = df_branches[df_branches['LocationType'] == 'Airport']
        city_branches = df_branches[df_branches['LocationType'] == 'City']
        
        print(f"\nAirport Branches:  {len(airport_branches)} branches, Avg: {airport_branches['AvgPrice'].mean():.2f} SAR")
        print(f"City Branches:     {len(city_branches)} branches, Avg: {city_branches['AvgPrice'].mean():.2f} SAR")
        
        location_premium = (airport_branches['AvgPrice'].mean() / city_branches['AvgPrice'].mean() - 1) * 100
        print(f"Location Premium:  {location_premium:+.1f}% (Airport vs City)")
        
        print("\nTop 5 Most Expensive Branches:")
        top_branches = df_branches.nlargest(5, 'AvgPrice')[['PickupBranchId', 'LocationType', 'AvgPrice', 'Contracts']]
        for _, row in top_branches.iterrows():
            print(f"  Branch {row['PickupBranchId']}: {row['AvgPrice']:.0f} SAR ({row['LocationType']}, {row['Contracts']:,} contracts)")
        
        # ================================================================
        # ANALYSIS: Compare with Hard-Coded Prices
        # ================================================================
        print("\n\n" + "="*100)
        print("COMPARISON: HARD-CODED vs DATABASE REALITY")
        print("="*100)
        
        hard_coded_prices = {
            'Economy': 150,
            'Compact': 180,
            'Standard': 220,
            'SUV Compact': 280,
            'SUV Standard': 350,
            'SUV Large': 500,
            'Luxury Sedan': 600,
            'Luxury SUV': 800
        }
        
        print("\nCurrent Dashboard (Hard-Coded):")
        for cat, price in hard_coded_prices.items():
            print(f"  {cat:20s}: {price:4.0f} SAR")
        
        print(f"\nDatabase Reality:")
        print(f"  Average ALL contracts: {avg_price:.2f} SAR")
        print(f"  Median (50th %ile):    {p50:.2f} SAR")
        print(f"  Lower Range (25th):    {p25:.2f} SAR")
        print(f"  Upper Range (75th):    {p75:.2f} SAR")
        
        print("\nAnalysis:")
        hc_avg = np.mean(list(hard_coded_prices.values()))
        print(f"  Hard-Coded Average:    {hc_avg:.2f} SAR")
        print(f"  Database Average:      {avg_price:.2f} SAR")
        print(f"  Difference:            {(avg_price - hc_avg):+.2f} SAR ({((avg_price/hc_avg-1)*100):+.1f}%)")
        
        # Check if hard-coded prices are in reasonable range
        print("\nValidation:")
        if p25 <= hc_avg <= p75:
            print(f"  [OK] Hard-coded average ({hc_avg:.0f} SAR) is within database range ({p25:.0f}-{p75:.0f} SAR)")
        else:
            print(f"  [WARNING] Hard-coded average ({hc_avg:.0f} SAR) is OUTSIDE database range ({p25:.0f}-{p75:.0f} SAR)")
        
        # ================================================================
        # RECOMMENDATIONS
        # ================================================================
        print("\n\n" + "="*100)
        print("RECOMMENDATIONS FOR BASE PRICES")
        print("="*100)
        
        print("\nOption A: USE DATABASE MEDIAN (Simple)")
        print("-"*50)
        print(f"  Set all base prices to: {p50:.0f} SAR")
        print(f"  Then let multipliers adjust by category/location/events")
        print(f"  Pro: Based on real data")
        print(f"  Con: Doesn't differentiate by vehicle category")
        
        print("\nOption B: USE PRICE DISTRIBUTION (Recommended)")
        print("-"*50)
        # Estimate category pricing based on distribution
        # Assuming Economy/Compact are lower end, Standard/SUV mid, Luxury upper
        economy_estimate = p25
        compact_estimate = (p25 + p50) / 2
        standard_estimate = p50
        suv_compact_estimate = (p50 + p75) / 2
        suv_standard_estimate = p75
        suv_large_estimate = (p75 + p90) / 2
        luxury_sedan_estimate = p90
        luxury_suv_estimate = p90 * 1.2
        
        recommendations = {
            'Economy': economy_estimate,
            'Compact': compact_estimate,
            'Standard': standard_estimate,
            'SUV Compact': suv_compact_estimate,
            'SUV Standard': suv_standard_estimate,
            'SUV Large': suv_large_estimate,
            'Luxury Sedan': luxury_sedan_estimate,
            'Luxury SUV': luxury_suv_estimate
        }
        
        for cat, rec_price in recommendations.items():
            hc_price = hard_coded_prices[cat]
            diff = rec_price - hc_price
            pct_diff = (diff / hc_price) * 100
            status = "INCREASE" if diff > 10 else ("DECREASE" if diff < -10 else "KEEP")
            print(f"  {cat:20s}: {rec_price:5.0f} SAR (vs {hc_price:4.0f} hard-coded) {pct_diff:+6.1f}% [{status}]")
        
        print("\nOption C: MANUAL VALIDATION (Most Accurate)")
        print("-"*50)
        print("  1. Identify actual vehicle categories in database")
        print("  2. Calculate median price per category")
        print("  3. Use category-specific real prices")
        print("  Pro: Most accurate")
        print("  Con: Requires category mapping (Models table doesn't exist)")
        
        # ================================================================
        # SAVE RESULTS
        # ================================================================
        print("\n\n" + "="*100)
        print("SAVING RESULTS")
        print("="*100)
        
        results = {
            'extraction_date': datetime.now().isoformat(),
            'total_contracts': total_contracts,
            'overall_stats': {
                'mean': float(avg_price),
                'median': float(p50),
                'p25': float(p25),
                'p75': float(p75),
                'p90': float(p90),
            },
            'weekend_analysis': df_weekend.to_dict('records'),
            'hard_coded_prices': hard_coded_prices,
            'recommended_prices': {k: float(v) for k, v in recommendations.items()},
            'location_premium': float(location_premium),
            'weekend_premium': float(weekend_premium) if len(df_weekend) == 2 else None,
        }
        
        with open('data/real_prices_from_database.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("Results saved to:")
        print("  - data/real_prices_from_database.json")
        print("  - data/branch_prices.csv")
        
        print("\n" + "="*100)
        print("EXTRACTION COMPLETE")
        print("="*100)

except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

