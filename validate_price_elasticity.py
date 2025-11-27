"""
PRICING DATA VALIDATION ANALYSIS
=================================

Critical validation before deploying hybrid pricing system:
1. Check if prices varied enough for V5 to learn elasticity
2. Measure actual price elasticity in historical data
3. Validate if V5 predictions align with real behavior
4. Determine if system is ready for production

If validated → integrate into dashboard
If not → recommendations for collecting pricing variation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)

print("="*100)
print("PRICING DATA VALIDATION ANALYSIS")
print("="*100)
print(f"Started at: {datetime.now()}")
print("="*100)

# ============================================================================
# PART 1: LOAD DATA
# ============================================================================
print("\n[PART 1] LOADING DATA")
print("-"*100)

df = pd.read_parquet('data/processed/training_data.parquet')
print(f"  Loaded: {len(df):,} contracts")

# Clean
df = df[df['DailyRateAmount'] > 0].copy()
df = df[df['DailyRateAmount'] < 10000].copy()
df['Date'] = pd.to_datetime(df['Start']).dt.date
df['Date'] = pd.to_datetime(df['Date'])

print(f"  After cleaning: {len(df):,} contracts")
print(f"  Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

# ============================================================================
# PART 2: PRICE VARIATION ANALYSIS
# ============================================================================
print("\n[PART 2] PRICE VARIATION ANALYSIS")
print("-"*100)

# Aggregate by branch-category-day
daily_agg = df.groupby(['Date', 'PickupBranchId', 'VehicleId']).agg({
    'DailyRateAmount': ['mean', 'std', 'count'],
    'Id': 'count'
}).reset_index()

daily_agg.columns = ['Date', 'BranchId', 'CategoryId', 'AvgPrice', 'StdPrice', 'PriceCount', 'Bookings']
daily_agg['StdPrice'] = daily_agg['StdPrice'].fillna(0)

print(f"\n  Total branch-category-day combinations: {len(daily_agg):,}")

# Overall price statistics
print(f"\n  OVERALL PRICE STATISTICS:")
print(f"    Mean price: {daily_agg['AvgPrice'].mean():.2f} SAR")
print(f"    Median price: {daily_agg['AvgPrice'].median():.2f} SAR")
print(f"    Std dev: {daily_agg['AvgPrice'].std():.2f} SAR")
print(f"    Min: {daily_agg['AvgPrice'].min():.2f} SAR")
print(f"    Max: {daily_agg['AvgPrice'].max():.2f} SAR")
print(f"    Coefficient of Variation: {(daily_agg['AvgPrice'].std() / daily_agg['AvgPrice'].mean()):.2%}")

# Price variation over time
daily_agg_sorted = daily_agg.sort_values('Date')
daily_agg_sorted['PriceChange'] = daily_agg_sorted.groupby(['BranchId', 'CategoryId'])['AvgPrice'].diff()
daily_agg_sorted['PriceChangePct'] = (daily_agg_sorted['PriceChange'] / daily_agg_sorted['AvgPrice'].shift(1)) * 100

price_changes = daily_agg_sorted.dropna(subset=['PriceChangePct'])

print(f"\n  PRICE CHANGES (Day-to-Day):")
print(f"    Days with price changes: {len(price_changes[price_changes['PriceChange'] != 0]):,} ({len(price_changes[price_changes['PriceChange'] != 0])/len(price_changes)*100:.1f}%)")
print(f"    Days with no change: {len(price_changes[price_changes['PriceChange'] == 0]):,} ({len(price_changes[price_changes['PriceChange'] == 0])/len(price_changes)*100:.1f}%)")
print(f"    Average absolute change: {price_changes['PriceChange'].abs().mean():.2f} SAR")
print(f"    Average absolute % change: {price_changes['PriceChangePct'].abs().mean():.2f}%")

# Check if prices varied enough
cv = daily_agg['AvgPrice'].std() / daily_agg['AvgPrice'].mean()
change_rate = len(price_changes[price_changes['PriceChange'] != 0]) / len(price_changes)

print(f"\n  VARIATION ASSESSMENT:")
if cv > 0.30 and change_rate > 0.30:
    print(f"    [EXCELLENT] High price variation (CV={cv:.2%}, Change Rate={change_rate:.1%})")
    print(f"                Sufficient for learning elasticity")
    variation_status = "EXCELLENT"
elif cv > 0.20 and change_rate > 0.20:
    print(f"    [GOOD] Moderate price variation (CV={cv:.2%}, Change Rate={change_rate:.1%})")
    print(f"           Should be able to learn some elasticity")
    variation_status = "GOOD"
elif cv > 0.10 and change_rate > 0.10:
    print(f"    [WEAK] Low price variation (CV={cv:.2%}, Change Rate={change_rate:.1%})")
    print(f"           Limited ability to learn elasticity")
    variation_status = "WEAK"
else:
    print(f"    [INSUFFICIENT] Very low variation (CV={cv:.2%}, Change Rate={change_rate:.1%})")
    print(f"                   Cannot reliably learn elasticity")
    variation_status = "INSUFFICIENT"

# ============================================================================
# PART 3: PRICE ELASTICITY MEASUREMENT
# ============================================================================
print("\n[PART 3] ACTUAL PRICE ELASTICITY MEASUREMENT")
print("-"*100)

# Prepare data for elasticity analysis
elasticity_data = daily_agg_sorted[daily_agg_sorted['Bookings'] > 0].copy()

# Calculate log-log regression (elasticity formula)
# Elasticity = % change in demand / % change in price
elasticity_data['LogPrice'] = np.log(elasticity_data['AvgPrice'])
elasticity_data['LogDemand'] = np.log(elasticity_data['Bookings'])

# Remove inf/nan
elasticity_data = elasticity_data.replace([np.inf, -np.inf], np.nan).dropna(subset=['LogPrice', 'LogDemand'])

if len(elasticity_data) > 100:
    # Overall elasticity (simple linear regression on logs)
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        elasticity_data['LogPrice'], 
        elasticity_data['LogDemand']
    )
    
    print(f"\n  LOG-LOG REGRESSION (Overall Elasticity):")
    print(f"    Price Elasticity: {slope:.3f}")
    print(f"    R²: {r_value**2:.4f}")
    print(f"    P-value: {p_value:.4e}")
    print(f"    Std Error: {std_err:.4f}")
    
    # Interpret elasticity
    print(f"\n  INTERPRETATION:")
    if abs(slope) < 0.1:
        print(f"    [INELASTIC] Demand barely responds to price changes")
        print(f"                A 10% price increase -> {abs(slope)*10:.1f}% demand change")
        elasticity_category = "INELASTIC"
    elif abs(slope) < 0.5:
        print(f"    [SLIGHTLY ELASTIC] Demand responds somewhat to prices")
        print(f"                       A 10% price increase -> {abs(slope)*10:.1f}% demand change")
        elasticity_category = "SLIGHTLY_ELASTIC"
    elif abs(slope) < 1.0:
        print(f"    [MODERATELY ELASTIC] Demand is price-sensitive")
        print(f"                         A 10% price increase -> {abs(slope)*10:.1f}% demand change")
        elasticity_category = "MODERATELY_ELASTIC"
    else:
        print(f"    [HIGHLY ELASTIC] Demand is very price-sensitive")
        print(f"                     A 10% price increase -> {abs(slope)*10:.1f}% demand change")
        elasticity_category = "HIGHLY_ELASTIC"
    
    if p_value < 0.05:
        print(f"    [SIGNIFICANT] Statistical significance confirmed (p < 0.05)")
        elasticity_significance = "SIGNIFICANT"
    else:
        print(f"    [NOT SIGNIFICANT] Relationship may be due to chance (p = {p_value:.4f})")
        elasticity_significance = "NOT_SIGNIFICANT"
else:
    print(f"  [ERROR] Insufficient data for elasticity calculation")
    slope = 0
    r_value = 0
    elasticity_category = "UNKNOWN"
    elasticity_significance = "UNKNOWN"

# ============================================================================
# PART 4: SEGMENT-LEVEL ELASTICITY
# ============================================================================
print("\n[PART 4] ELASTICITY BY SEGMENT")
print("-"*100)

# Top branches by volume
top_branches = df.groupby('PickupBranchId').size().nlargest(5).index

print(f"\n  Analyzing top 5 branches...")
segment_elasticities = []

for branch in top_branches:
    branch_data = elasticity_data[elasticity_data['BranchId'] == branch].copy()
    
    if len(branch_data) > 30:
        slope_b, _, r_b, p_b, _ = stats.linregress(
            branch_data['LogPrice'], 
            branch_data['LogDemand']
        )
        
        segment_elasticities.append({
            'Branch': branch,
            'Elasticity': slope_b,
            'R2': r_b**2,
            'P_value': p_b,
            'N_days': len(branch_data)
        })
        
        print(f"    Branch {branch}: Elasticity = {slope_b:.3f}, R² = {r_b**2:.4f}, p = {p_b:.4f}")

df_segments = pd.DataFrame(segment_elasticities)

if len(df_segments) > 0:
    print(f"\n  SEGMENT SUMMARY:")
    print(f"    Average elasticity: {df_segments['Elasticity'].mean():.3f}")
    print(f"    Std dev: {df_segments['Elasticity'].std():.3f}")
    print(f"    Range: [{df_segments['Elasticity'].min():.3f}, {df_segments['Elasticity'].max():.3f}]")

# ============================================================================
# PART 5: PRICE-DEMAND RELATIONSHIP VISUALIZATION
# ============================================================================
print("\n[PART 5] GENERATING VISUALIZATIONS")
print("-"*100)

fig = plt.figure(figsize=(18, 12))

# 1. Price distribution over time
ax1 = plt.subplot(3, 3, 1)
monthly_prices = daily_agg.groupby(daily_agg['Date'].dt.to_period('M'))['AvgPrice'].agg(['mean', 'std'])
monthly_prices.index = monthly_prices.index.to_timestamp()
ax1.plot(monthly_prices.index, monthly_prices['mean'], marker='o', linewidth=2, color='steelblue')
ax1.fill_between(monthly_prices.index, 
                  monthly_prices['mean'] - monthly_prices['std'],
                  monthly_prices['mean'] + monthly_prices['std'],
                  alpha=0.3, color='steelblue')
ax1.set_title('Average Price Over Time (± 1 Std Dev)', fontweight='bold')
ax1.set_xlabel('Month')
ax1.set_ylabel('Price (SAR)')
ax1.grid(alpha=0.3)

# 2. Price change distribution
ax2 = plt.subplot(3, 3, 2)
ax2.hist(price_changes['PriceChangePct'].clip(-50, 50), bins=50, color='coral', alpha=0.7, edgecolor='black')
ax2.axvline(x=0, color='red', linestyle='--', linewidth=2, label='No Change')
ax2.set_title('Distribution of Price Changes (%)', fontweight='bold')
ax2.set_xlabel('Price Change (%)')
ax2.set_ylabel('Frequency')
ax2.legend()
ax2.grid(alpha=0.3)

# 3. Price coefficient of variation by branch
ax3 = plt.subplot(3, 3, 3)
branch_cv = daily_agg.groupby('BranchId')['AvgPrice'].agg(lambda x: x.std() / x.mean()).sort_values(ascending=False).head(10)
ax3.barh(range(len(branch_cv)), branch_cv.values, color='green', alpha=0.7)
ax3.set_yticks(range(len(branch_cv)))
ax3.set_yticklabels([f'Branch {int(b)}' for b in branch_cv.index])
ax3.set_title('Top 10 Branches by Price Variation (CV)', fontweight='bold')
ax3.set_xlabel('Coefficient of Variation')
ax3.grid(axis='x', alpha=0.3)

# 4. Price vs Demand scatter (overall)
ax4 = plt.subplot(3, 3, 4)
sample_data = elasticity_data.sample(min(5000, len(elasticity_data)))
ax4.scatter(sample_data['AvgPrice'], sample_data['Bookings'], alpha=0.3, s=10, color='steelblue')
if len(elasticity_data) > 100:
    # Add regression line
    z = np.polyfit(elasticity_data['AvgPrice'], elasticity_data['Bookings'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(elasticity_data['AvgPrice'].min(), elasticity_data['AvgPrice'].max(), 100)
    ax4.plot(x_line, p(x_line), "r--", linewidth=2, label=f'Trend (slope={z[0]:.4f})')
    ax4.legend()
ax4.set_title('Price vs Demand (Overall)', fontweight='bold')
ax4.set_xlabel('Average Price (SAR)')
ax4.set_ylabel('Daily Bookings')
ax4.grid(alpha=0.3)

# 5. Log-log elasticity plot
ax5 = plt.subplot(3, 3, 5)
sample_data_log = elasticity_data.sample(min(5000, len(elasticity_data)))
ax5.scatter(sample_data_log['LogPrice'], sample_data_log['LogDemand'], alpha=0.3, s=10, color='coral')
if len(elasticity_data) > 100:
    ax5.plot(elasticity_data['LogPrice'], 
             intercept + slope * elasticity_data['LogPrice'], 
             'r--', linewidth=2, 
             label=f'Elasticity={slope:.3f}, R²={r_value**2:.4f}')
    ax5.legend()
ax5.set_title('Log-Log Elasticity Analysis', fontweight='bold')
ax5.set_xlabel('Log(Price)')
ax5.set_ylabel('Log(Demand)')
ax5.grid(alpha=0.3)

# 6. Elasticity by segment
ax6 = plt.subplot(3, 3, 6)
if len(df_segments) > 0:
    colors = ['green' if e < -0.5 else 'orange' if e < -0.2 else 'red' for e in df_segments['Elasticity']]
    ax6.barh(range(len(df_segments)), df_segments['Elasticity'].values, color=colors, alpha=0.7)
    ax6.set_yticks(range(len(df_segments)))
    ax6.set_yticklabels([f"Branch {int(b)}" for b in df_segments['Branch']])
    ax6.axvline(x=-1, color='green', linestyle='--', alpha=0.5, label='Unitary Elastic')
    ax6.axvline(x=-0.5, color='orange', linestyle='--', alpha=0.5, label='Moderately Elastic')
    ax6.legend()
ax6.set_title('Price Elasticity by Branch', fontweight='bold')
ax6.set_xlabel('Elasticity (negative = demand decreases with price)')
ax6.grid(axis='x', alpha=0.3)

# 7. Days with price changes over time
ax7 = plt.subplot(3, 3, 7)
monthly_changes = price_changes.groupby(price_changes['Date'].dt.to_period('M')).apply(
    lambda x: (x['PriceChange'] != 0).sum() / len(x) * 100
)
monthly_changes.index = monthly_changes.index.to_timestamp()
ax7.plot(monthly_changes.index, monthly_changes.values, marker='o', linewidth=2, color='purple')
ax7.set_title('% of Days with Price Changes (Monthly)', fontweight='bold')
ax7.set_xlabel('Month')
ax7.set_ylabel('% Days with Changes')
ax7.grid(alpha=0.3)

# 8. Price volatility over time
ax8 = plt.subplot(3, 3, 8)
monthly_volatility = daily_agg.groupby(daily_agg['Date'].dt.to_period('M'))['AvgPrice'].std()
monthly_volatility.index = monthly_volatility.index.to_timestamp()
ax8.plot(monthly_volatility.index, monthly_volatility.values, marker='o', linewidth=2, color='darkred')
ax8.set_title('Price Volatility Over Time (Std Dev)', fontweight='bold')
ax8.set_xlabel('Month')
ax8.set_ylabel('Std Dev (SAR)')
ax8.grid(alpha=0.3)

# 9. Summary metrics box
ax9 = plt.subplot(3, 3, 9)
ax9.axis('off')
summary_text = f"""
VALIDATION SUMMARY
================================

Price Variation: {variation_status}
  - CV: {cv:.2%}
  - Change Rate: {change_rate:.1%}

Price Elasticity: {elasticity_category}
  - Overall: {slope:.3f}
  - R2: {r_value**2:.4f}
  - Significance: {elasticity_significance}

Sample Size:
  - Total days: {len(daily_agg):,}
  - With changes: {len(price_changes[price_changes['PriceChange'] != 0]):,}

Recommendation:
  {variation_status} variation
  {elasticity_significance} elasticity
"""
ax9.text(0.1, 0.5, summary_text, fontsize=10, family='monospace',
         verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
plt.savefig('visualizations/price_elasticity_validation.png', dpi=150, bbox_inches='tight')
print("  [OK] Saved: visualizations/price_elasticity_validation.png")

# ============================================================================
# PART 6: FINAL VERDICT
# ============================================================================
print("\n" + "="*100)
print("FINAL VALIDATION VERDICT")
print("="*100)

# Scoring system
variation_score = 0
if variation_status == "EXCELLENT":
    variation_score = 4
elif variation_status == "GOOD":
    variation_score = 3
elif variation_status == "WEAK":
    variation_score = 2
else:
    variation_score = 1

elasticity_score = 0
if elasticity_significance == "SIGNIFICANT":
    elasticity_score = 4
elif abs(slope) > 0.1:
    elasticity_score = 2
else:
    elasticity_score = 1

total_score = variation_score + elasticity_score
max_score = 8

print(f"\n[VALIDATION SCORES]")
print(f"  Price Variation: {variation_score}/4")
print(f"  Elasticity Signal: {elasticity_score}/4")
print(f"  TOTAL: {total_score}/{max_score} ({total_score/max_score*100:.0f}%)")

print(f"\n[RECOMMENDATION]")
if total_score >= 6:
    print("  [OK] APPROVED FOR PRODUCTION")
    print("    - Sufficient price variation in historical data")
    print("    - Detectable price elasticity signal")
    print("    - Hybrid system ready for dashboard integration")
    print("")
    print("  NEXT STEPS:")
    print("    1. Integrate hybrid engine into dashboard")
    print("    2. Set up A/B test on 2-3 branches")
    print("    3. Monitor predicted vs actual elasticity")
    print("    4. Full rollout after 2-week validation")
    recommendation = "APPROVED"
    
elif total_score >= 4:
    print("  [WARNING] CONDITIONAL APPROVAL")
    print("    - Some price variation exists")
    print("    - Elasticity signal is weak but present")
    print("    - Can proceed with caution")
    print("")
    print("  NEXT STEPS:")
    print("    1. Integrate with LOW CONFIDENCE warnings")
    print("    2. Use wider elasticity bounds (0.7-1.3)")
    print("    3. Collect more pricing variation data")
    print("    4. Re-validate in 1 month")
    recommendation = "CONDITIONAL"
    
else:
    print("  [FAIL] NOT READY FOR PRODUCTION")
    print("    - Insufficient price variation")
    print("    - No reliable elasticity signal")
    print("    - Risk: Model will default to baseline (V4 only)")
    print("")
    print("  RECOMMENDATIONS:")
    print("    1. Implement systematic pricing experiments:")
    print("       - Vary prices by +/-10-20% across branches")
    print("       - Run for 3-6 months to collect data")
    print("       - Test different days of week")
    print("    2. Use V4 (baseline) only for now")
    print("    3. Re-run validation after collecting data")
    recommendation = "NOT_READY"

# Generate report
print(f"\n[GENERATING VALIDATION REPORT]")
with open('PRICE_ELASTICITY_VALIDATION_REPORT.txt', 'w') as f:
    f.write("="*80 + "\n")
    f.write("PRICE ELASTICITY VALIDATION REPORT\n")
    f.write("="*80 + "\n")
    f.write(f"Analysis Date: {datetime.now()}\n")
    f.write(f"Data Period: {df['Date'].min().date()} to {df['Date'].max().date()}\n")
    f.write(f"Sample Size: {len(df):,} contracts, {len(daily_agg):,} branch-category-days\n\n")
    
    f.write("PRICE VARIATION ANALYSIS:\n")
    f.write(f"  Coefficient of Variation: {cv:.2%}\n")
    f.write(f"  Days with Price Changes: {change_rate:.1%}\n")
    f.write(f"  Average Absolute Change: {price_changes['PriceChangePct'].abs().mean():.2f}%\n")
    f.write(f"  Status: {variation_status}\n\n")
    
    f.write("PRICE ELASTICITY MEASUREMENT:\n")
    f.write(f"  Overall Elasticity: {slope:.3f}\n")
    f.write(f"  R²: {r_value**2:.4f}\n")
    f.write(f"  P-value: {p_value:.4e}\n")
    f.write(f"  Category: {elasticity_category}\n")
    f.write(f"  Significance: {elasticity_significance}\n\n")
    
    f.write("VALIDATION SCORES:\n")
    f.write(f"  Price Variation: {variation_score}/4\n")
    f.write(f"  Elasticity Signal: {elasticity_score}/4\n")
    f.write(f"  TOTAL: {total_score}/{max_score} ({total_score/max_score*100:.0f}%)\n\n")
    
    f.write("FINAL RECOMMENDATION:\n")
    f.write(f"  Status: {recommendation}\n\n")
    
    f.write("="*80 + "\n")

print("  [OK] Saved: PRICE_ELASTICITY_VALIDATION_REPORT.txt")

print("\n" + "="*100)
print(f"Completed at: {datetime.now()}")
print("="*100)

