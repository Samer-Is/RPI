"""
MODEL V5: BUSINESS-FOCUSED DEMAND FORECASTING
==============================================

Key Improvements:
1. Add lag features (7d, 14d, 30d historical demand)
2. Test price elasticity explicitly
3. Enhanced seasonality features
4. Remove reliance on branch/city identifiers
5. Focus on actionable features for pricing decisions

Goal: Build a model that helps make PRICING DECISIONS, not just forecasts demand
"""

import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
from xgboost import XGBRegressor
import warnings
warnings.filterwarnings('ignore')

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

print("="*100)
print("MODEL V5: BUSINESS-FOCUSED DEMAND FORECASTING")
print("="*100)
print(f"Started at: {datetime.now()}")
print("="*100)

# ============================================================================
# PART 1: LOAD AND PREPARE DATA
# ============================================================================
print("\n[PART 1] DATA LOADING")
print("-"*100)

df = pd.read_parquet('data/processed/training_data.parquet')
print(f"  Loaded: {len(df):,} contracts")

# Clean data
df = df[df['DailyRateAmount'] > 0].copy()
df = df[df['DailyRateAmount'] < 10000].copy()
df['Date'] = pd.to_datetime(df['Start']).dt.date
df['Date'] = pd.to_datetime(df['Date'])
print(f"  After cleaning: {len(df):,} contracts")

# Create target: daily booking count per branch+category
print("\n  Creating target variable (daily bookings per branch + category)...")
df['CategoryId'] = df['VehicleId']  # Using VehicleId as category proxy
demand_counts = df.groupby(['Date', 'PickupBranchId', 'CategoryId']).agg({
    'DailyRateAmount': ['mean', 'std', 'count']
}).reset_index()

demand_counts.columns = ['Date', 'BranchId', 'CategoryId', 'AvgPrice', 'StdPrice', 'DailyBookings']
demand_counts['StdPrice'] = demand_counts['StdPrice'].fillna(0)

print(f"  Created {len(demand_counts):,} branch-category-day combinations")
print(f"  Target: DailyBookings")
print(f"    Mean: {demand_counts['DailyBookings'].mean():.2f} bookings/day")
print(f"    Median: {demand_counts['DailyBookings'].median():.1f} bookings/day")

# ============================================================================
# PART 2: FEATURE ENGINEERING - BUSINESS FOCUSED
# ============================================================================
print("\n[PART 2] FEATURE ENGINEERING - BUSINESS FOCUSED")
print("-"*100)

df_features = demand_counts.copy()

# 2.1 TEMPORAL FEATURES
print("\n[2.1] Temporal features...")
df_features['DayOfWeek'] = df_features['Date'].dt.dayofweek
df_features['DayOfMonth'] = df_features['Date'].dt.day
df_features['WeekOfYear'] = df_features['Date'].dt.isocalendar().week.astype(int)
df_features['Month'] = df_features['Date'].dt.month
df_features['Quarter'] = df_features['Date'].dt.quarter
df_features['IsWeekend'] = df_features['DayOfWeek'].isin([5, 6]).astype(int)
df_features['DayOfYear'] = df_features['Date'].dt.dayofyear

# Fourier features for seasonality
for period, k_max in [(7, 3), (30, 2), (365, 3)]:
    for k in range(1, k_max + 1):
        df_features[f'sin_{period}_{k}'] = np.sin(2 * np.pi * k * df_features['DayOfYear'] / period)
        df_features[f'cos_{period}_{k}'] = np.cos(2 * np.pi * k * df_features['DayOfYear'] / period)

print(f"  [OK] Temporal + Fourier features created")

# 2.2 PRICE FEATURES - CRITICAL FOR PRICING DECISIONS
print("\n[2.2] Price features (for elasticity learning)...")

# Sort by branch, category, date for lag calculations
df_features = df_features.sort_values(['BranchId', 'CategoryId', 'Date']).reset_index(drop=True)

# Price change signals
df_features['Price_Lag_1d'] = df_features.groupby(['BranchId', 'CategoryId'])['AvgPrice'].shift(1)
df_features['Price_Lag_7d'] = df_features.groupby(['BranchId', 'CategoryId'])['AvgPrice'].shift(7)
df_features['Price_Change_1d'] = df_features['AvgPrice'] - df_features['Price_Lag_1d']
df_features['Price_Change_7d'] = df_features['AvgPrice'] - df_features['Price_Lag_7d']
df_features['Price_Change_Pct_1d'] = (df_features['Price_Change_1d'] / df_features['Price_Lag_1d'].clip(lower=1)) * 100
df_features['Price_Change_Pct_7d'] = (df_features['Price_Change_7d'] / df_features['Price_Lag_7d'].clip(lower=1)) * 100

# Price relative to historical average
df_features['Price_vs_BranchAvg'] = df_features.groupby('BranchId')['AvgPrice'].transform(
    lambda x: (x - x.expanding().mean().shift(1)) / x.expanding().mean().shift(1).clip(lower=1)
)
df_features['Price_vs_CategoryAvg'] = df_features.groupby('CategoryId')['AvgPrice'].transform(
    lambda x: (x - x.expanding().mean().shift(1)) / x.expanding().mean().shift(1).clip(lower=1)
)

# Price volatility
df_features['Price_Volatility_7d'] = df_features.groupby(['BranchId', 'CategoryId'])['AvgPrice'].transform(
    lambda x: x.rolling(7, min_periods=1).std()
)

print(f"  [OK] Price elasticity features created")

# 2.3 LAG FEATURES - HISTORICAL DEMAND PATTERNS
print("\n[2.3] Lag features (historical demand)...")

# Direct lags
for lag in [1, 2, 3, 7, 14, 21, 30]:
    df_features[f'Demand_Lag_{lag}d'] = df_features.groupby(['BranchId', 'CategoryId'])['DailyBookings'].shift(lag)

# Rolling averages
for window in [3, 7, 14, 30]:
    df_features[f'Demand_RollMean_{window}d'] = df_features.groupby(['BranchId', 'CategoryId'])['DailyBookings'].transform(
        lambda x: x.shift(1).rolling(window, min_periods=1).mean()
    )
    df_features[f'Demand_RollStd_{window}d'] = df_features.groupby(['BranchId', 'CategoryId'])['DailyBookings'].transform(
        lambda x: x.shift(1).rolling(window, min_periods=1).std()
    )

# Demand trend
df_features['Demand_Trend_7d'] = df_features['Demand_Lag_1d'] - df_features['Demand_Lag_7d']
df_features['Demand_Trend_30d'] = df_features['Demand_Lag_7d'] - df_features['Demand_Lag_30d']

# Day-of-week specific patterns
df_features['Demand_SameDayLastWeek'] = df_features.groupby(['BranchId', 'CategoryId'])['DailyBookings'].shift(7)
df_features['Demand_SameDayLast2Weeks'] = df_features.groupby(['BranchId', 'CategoryId'])['DailyBookings'].shift(14)

print(f"  [OK] Lag and rolling features created")

# 2.4 EXTERNAL FEATURES (HOLIDAYS, EVENTS)
print("\n[2.4] External features (holidays/events)...")
try:
    from external_data_fetcher import create_holiday_features
    start_date = df_features['Date'].min()
    end_date = df_features['Date'].max()
    df_holidays = create_holiday_features(start_date=start_date, end_date=end_date)
    df_features = df_features.merge(df_holidays, left_on='Date', right_on='date', how='left')
    
    # Enhanced holiday features
    df_features['is_long_holiday'] = (df_features['holiday_duration'] >= 4).astype(int)
    df_features['near_holiday'] = ((df_features['days_to_holiday'] >= 0) & (df_features['days_to_holiday'] <= 2)).astype(int)
    df_features['post_holiday'] = ((df_features['days_from_holiday'] >= 0) & (df_features['days_from_holiday'] <= 2)).astype(int)
    
    print(f"  [OK] External features loaded")
    
except Exception as e:
    print(f"  [WARNING] Could not load external features: {str(e)}")
    # Create dummy features
    for feat in ['is_holiday', 'holiday_duration', 'is_school_vacation', 'is_ramadan', 
                 'is_umrah_season', 'umrah_season_intensity', 'is_major_event', 'is_hajj',
                 'is_festival', 'is_sports_event', 'days_to_holiday', 'days_from_holiday',
                 'is_long_holiday', 'near_holiday', 'post_holiday']:
        df_features[feat] = 0

# Convert umrah_season_intensity to numeric if it's object
if 'umrah_season_intensity' in df_features.columns and df_features['umrah_season_intensity'].dtype == 'object':
    df_features['umrah_season_intensity'] = pd.to_numeric(df_features['umrah_season_intensity'], errors='coerce').fillna(0)

# 2.5 CONTEXTUAL FEATURES (NOT BRANCH/CITY IDs)
print("\n[2.5] Contextual features...")

# Branch size bucket (instead of branch ID)
branch_sizes = df_features.groupby('BranchId')['DailyBookings'].mean()
df_features['BranchSizeBucket'] = df_features['BranchId'].map(branch_sizes).apply(
    lambda x: 0 if x < 20 else (1 if x < 50 else (2 if x < 100 else 3))
)

# Category popularity bucket
category_popularity = df_features.groupby('CategoryId')['DailyBookings'].mean()
df_features['CategoryPopularityBucket'] = df_features['CategoryId'].map(category_popularity).apply(
    lambda x: 0 if x < 10 else (1 if x < 30 else (2 if x < 60 else 3))
)

print(f"  [OK] Contextual features created (using buckets, not IDs)")

# ============================================================================
# PART 3: PREPARE DATASETS
# ============================================================================
print("\n[PART 3] PREPARING DATASETS")
print("-"*100)

# Define feature columns - EXCLUDING branch/city identifiers
feature_cols = [
    # Temporal
    'DayOfWeek', 'Month', 'Quarter', 'IsWeekend', 'DayOfYear', 'WeekOfYear',
    
    # Fourier (seasonality)
    'sin_7_1', 'cos_7_1', 'sin_7_2', 'cos_7_2', 'sin_7_3', 'cos_7_3',
    'sin_30_1', 'cos_30_1', 'sin_30_2', 'cos_30_2',
    'sin_365_1', 'cos_365_1', 'sin_365_2', 'cos_365_2', 'sin_365_3', 'cos_365_3',
    
    # Price features (CRITICAL)
    'AvgPrice', 'StdPrice',
    'Price_Change_1d', 'Price_Change_7d',
    'Price_Change_Pct_1d', 'Price_Change_Pct_7d',
    'Price_vs_BranchAvg', 'Price_vs_CategoryAvg',
    'Price_Volatility_7d',
    
    # Lag features (historical demand)
    'Demand_Lag_1d', 'Demand_Lag_2d', 'Demand_Lag_3d', 'Demand_Lag_7d', 
    'Demand_Lag_14d', 'Demand_Lag_21d', 'Demand_Lag_30d',
    'Demand_RollMean_3d', 'Demand_RollMean_7d', 'Demand_RollMean_14d', 'Demand_RollMean_30d',
    'Demand_RollStd_3d', 'Demand_RollStd_7d', 'Demand_RollStd_14d', 'Demand_RollStd_30d',
    'Demand_Trend_7d', 'Demand_Trend_30d',
    'Demand_SameDayLastWeek', 'Demand_SameDayLast2Weeks',
    
    # External features
    'is_holiday', 'holiday_duration', 'is_school_vacation', 'is_ramadan',
    'is_umrah_season', 'umrah_season_intensity', 'is_major_event', 'is_hajj',
    'is_festival', 'is_sports_event', 'days_to_holiday', 'days_from_holiday',
    'is_long_holiday', 'near_holiday', 'post_holiday',
    
    # Contextual (buckets, not IDs)
    'BranchSizeBucket', 'CategoryPopularityBucket'
]

# Filter to existing columns
feature_cols = [col for col in feature_cols if col in df_features.columns]
print(f"\n  Total features: {len(feature_cols)}")

# Show feature breakdown
feature_categories = {
    'Temporal/Seasonality': [f for f in feature_cols if any(x in f.lower() for x in ['day', 'week', 'month', 'quarter', 'sin', 'cos', 'year'])],
    'Price Features': [f for f in feature_cols if 'price' in f.lower()],
    'Demand Lags/History': [f for f in feature_cols if 'demand' in f.lower() or 'lag' in f.lower() or 'roll' in f.lower()],
    'Events/Holidays': [f for f in feature_cols if any(x in f.lower() for x in ['holiday', 'ramadan', 'hajj', 'umrah', 'event', 'festival'])],
    'Context': [f for f in feature_cols if 'bucket' in f.lower()]
}

for cat, feats in feature_categories.items():
    print(f"    {cat}: {len(feats)} features")

# Handle missing values
for col in feature_cols:
    if df_features[col].dtype in ['float64', 'int64']:
        df_features[col].fillna(df_features[col].median(), inplace=True)
    else:
        df_features[col] = pd.to_numeric(df_features[col], errors='coerce').fillna(0)

# Remove rows with insufficient lag data (first 30 days per branch-category)
print(f"\n  Removing rows with insufficient lag data...")
df_features['row_num'] = df_features.groupby(['BranchId', 'CategoryId']).cumcount()
df_features = df_features[df_features['row_num'] >= 30].copy()
print(f"  After filtering: {len(df_features):,} samples")

# Time-based split
df_sorted = df_features.sort_values('Date').reset_index(drop=True)
n = len(df_sorted)
train_idx = int(n * 0.70)
val_idx = int(n * 0.85)

df_train = df_sorted[:train_idx]
df_val = df_sorted[train_idx:val_idx]
df_test = df_sorted[val_idx:]

X_train = df_train[feature_cols]
y_train = df_train['DailyBookings']
X_val = df_val[feature_cols]
y_val = df_val['DailyBookings']
X_test = df_test[feature_cols]
y_test = df_test['DailyBookings']

print(f"\n  Data split (time-based):")
print(f"    Train: {len(df_train):,} ({len(df_train)/n*100:.1f}%) - {df_train['Date'].min().date()} to {df_train['Date'].max().date()}")
print(f"    Val:   {len(df_val):,} ({len(df_val)/n*100:.1f}%) - {df_val['Date'].min().date()} to {df_val['Date'].max().date()}")
print(f"    Test:  {len(df_test):,} ({len(df_test)/n*100:.1f}%) - {df_test['Date'].min().date()} to {df_test['Date'].max().date()}")

# ============================================================================
# PART 4: TRAIN MODEL
# ============================================================================
print("\n[PART 4] TRAINING BUSINESS-FOCUSED MODEL")
print("-"*100)

print("\n  Model configuration:")
print("    - Focus: Price elasticity + demand patterns")
print("    - NO branch/city IDs (only size buckets)")
print("    - Emphasis on actionable features")

model = XGBRegressor(
    objective='reg:squarederror',
    n_estimators=300,
    max_depth=5,
    learning_rate=0.1,
    min_child_weight=3,
    subsample=0.9,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.5,
    random_state=42,
    n_jobs=-1,
    early_stopping_rounds=20
)

print("\n  Training model...")
start_time = datetime.now()

model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=False
)

train_time = (datetime.now() - start_time).total_seconds()
print(f"  [OK] Training completed in {train_time:.1f} seconds")

# ============================================================================
# PART 5: EVALUATE MODEL
# ============================================================================
print("\n[PART 5] MODEL EVALUATION")
print("-"*100)

# Predictions
y_train_pred = model.predict(X_train)
y_val_pred = model.predict(X_val)
y_test_pred = model.predict(X_test)

# Metrics
train_metrics = {
    'r2': r2_score(y_train, y_train_pred),
    'rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
    'mae': mean_absolute_error(y_train, y_train_pred),
    'mape': mean_absolute_percentage_error(y_train, y_train_pred)
}

val_metrics = {
    'r2': r2_score(y_val, y_val_pred),
    'rmse': np.sqrt(mean_squared_error(y_val, y_val_pred)),
    'mae': mean_absolute_error(y_val, y_val_pred),
    'mape': mean_absolute_percentage_error(y_val, y_val_pred)
}

test_metrics = {
    'r2': r2_score(y_test, y_test_pred),
    'rmse': np.sqrt(mean_squared_error(y_test, y_test_pred)),
    'mae': mean_absolute_error(y_test, y_test_pred),
    'mape': mean_absolute_percentage_error(y_test, y_test_pred)
}

print("\n  PERFORMANCE METRICS:")
print(f"    Train - R²: {train_metrics['r2']:.4f}, RMSE: {train_metrics['rmse']:.2f}, MAE: {train_metrics['mae']:.2f}, MAPE: {train_metrics['mape']*100:.2f}%")
print(f"    Val   - R²: {val_metrics['r2']:.4f}, RMSE: {val_metrics['rmse']:.2f}, MAE: {val_metrics['mae']:.2f}, MAPE: {val_metrics['mape']*100:.2f}%")
print(f"    Test  - R²: {test_metrics['r2']:.4f}, RMSE: {test_metrics['rmse']:.2f}, MAE: {test_metrics['mae']:.2f}, MAPE: {test_metrics['mape']*100:.2f}%")

# Overfitting check
r2_gap = train_metrics['r2'] - test_metrics['r2']
print(f"\n  OVERFITTING CHECK:")
print(f"    Train-Test R² Gap: {r2_gap:.4f} ({r2_gap/train_metrics['r2']*100:.1f}%)")
if r2_gap < 0.05:
    print(f"    Status: [EXCELLENT] Gap < 5%")
elif r2_gap < 0.10:
    print(f"    Status: [GOOD] Gap < 10%")
else:
    print(f"    Status: [WARNING] Gap >= 10%")

# ============================================================================
# PART 6: FEATURE IMPORTANCE ANALYSIS
# ============================================================================
print("\n[PART 6] FEATURE IMPORTANCE ANALYSIS")
print("-"*100)

feature_importance = pd.DataFrame({
    'Feature': feature_cols,
    'Importance': model.feature_importances_
}).sort_values('Importance', ascending=False)

print("\nTop 20 features:")
print(feature_importance.head(20).to_string(index=False))

# Category analysis
def categorize_v5(feat):
    feat_lower = feat.lower()
    if 'price' in feat_lower:
        return 'Price Features'
    elif any(x in feat_lower for x in ['lag', 'roll', 'trend', 'sameday']):
        return 'Demand History'
    elif any(x in feat_lower for x in ['holiday', 'ramadan', 'hajj', 'umrah', 'event', 'festival']):
        return 'Events/Holidays'
    elif any(x in feat_lower for x in ['sin', 'cos']):
        return 'Seasonality (Fourier)'
    elif any(x in feat_lower for x in ['day', 'week', 'month', 'quarter', 'year']):
        return 'Temporal'
    elif 'bucket' in feat_lower:
        return 'Context (Buckets)'
    else:
        return 'Other'

feature_importance['Category'] = feature_importance['Feature'].apply(categorize_v5)
category_importance = feature_importance.groupby('Category')['Importance'].sum().sort_values(ascending=False)

print("\n\nFeature importance by category:")
for cat, imp in category_importance.items():
    print(f"  {cat:30} {imp:>6.2%}")

# Critical analysis
print("\n  CRITICAL ANALYSIS:")
price_importance = category_importance.get('Price Features', 0)
if price_importance < 0.05:
    print(f"  [WARNING] Price features contributing only {price_importance:.2%} - price elasticity still low")
elif price_importance < 0.15:
    print(f"  [CAUTION] Price features at {price_importance:.2%} - moderate price sensitivity")
else:
    print(f"  [GOOD] Price features at {price_importance:.2%} - model learning from prices")

history_importance = category_importance.get('Demand History', 0)
if history_importance < 0.10:
    print(f"  [WARNING] Demand history only {history_importance:.2%} - not learning from trends")
else:
    print(f"  [GOOD] Demand history at {history_importance:.2%} - learning from patterns")

# ============================================================================
# PART 7: SAVE MODEL
# ============================================================================
print("\n[PART 7] SAVING MODEL")
print("-"*100)

# Save model
with open('models/demand_prediction_v5_business.pkl', 'wb') as f:
    pickle.dump(model, f)
print("  [OK] Model saved: models/demand_prediction_v5_business.pkl")

# Save feature columns
with open('models/feature_columns_v5.pkl', 'wb') as f:
    pickle.dump(feature_cols, f)
print("  [OK] Features saved: models/feature_columns_v5.pkl")

# Save metrics
metrics_v5 = {
    'train': train_metrics,
    'val': val_metrics,
    'test': test_metrics,
    'feature_importance': feature_importance.to_dict(),
    'category_importance': category_importance.to_dict(),
    'training_date': datetime.now().isoformat()
}

with open('models/training_metrics_v5.pkl', 'wb') as f:
    pickle.dump(metrics_v5, f)
print("  [OK] Metrics saved: models/training_metrics_v5.pkl")

# ============================================================================
# PART 8: VISUALIZATIONS
# ============================================================================
print("\n[PART 8] GENERATING VISUALIZATIONS")
print("-"*100)

# 1. Feature importance by category
fig, axes = plt.subplots(1, 2, figsize=(18, 6))

categories = category_importance.head(6)
colors = ['#E63946', '#F77F00', '#06D6A0', '#118AB2', '#073B4C', '#FFB703']
axes[0].barh(categories.index, categories.values, color=colors, alpha=0.8)
axes[0].set_xlabel('Total Feature Importance', fontsize=12, fontweight='bold')
axes[0].set_title('V5 Model: Feature Importance by Category', fontsize=14, fontweight='bold')
axes[0].grid(axis='x', alpha=0.3)
for i, (cat, val) in enumerate(categories.items()):
    axes[0].text(val + 0.01, i, f'{val:.1%}', va='center', fontsize=10, fontweight='bold')

# 2. Top individual features
top_features = feature_importance.head(20)
colors_map = {
    'Price Features': '#E63946',
    'Demand History': '#F77F00',
    'Events/Holidays': '#06D6A0',
    'Seasonality (Fourier)': '#118AB2',
    'Temporal': '#073B4C',
    'Context (Buckets)': '#FFB703',
    'Other': '#999999'
}
feature_colors = [colors_map.get(cat, '#999999') for cat in top_features['Category']]
axes[1].barh(range(len(top_features)), top_features['Importance'], color=feature_colors, alpha=0.8)
axes[1].set_yticks(range(len(top_features)))
axes[1].set_yticklabels(top_features['Feature'], fontsize=9)
axes[1].set_xlabel('Feature Importance', fontsize=12, fontweight='bold')
axes[1].set_title('Top 20 Individual Features', fontsize=14, fontweight='bold')
axes[1].grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig('visualizations/v5_feature_importance.png', dpi=150, bbox_inches='tight')
print("  [OK] Saved: visualizations/v5_feature_importance.png")

# 2. Predictions vs Actual
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

axes[0].scatter(y_test, y_test_pred, alpha=0.3, s=10, color='steelblue')
axes[0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
axes[0].set_xlabel('Actual Bookings', fontsize=12, fontweight='bold')
axes[0].set_ylabel('Predicted Bookings', fontsize=12, fontweight='bold')
axes[0].set_title(f'Test Set: Actual vs Predicted\nR² = {test_metrics["r2"]:.4f}, MAE = {test_metrics["mae"]:.2f}', 
                  fontsize=14, fontweight='bold')
axes[0].grid(alpha=0.3)

# Residuals
residuals = y_test - y_test_pred
axes[1].scatter(y_test_pred, residuals, alpha=0.3, s=10, color='coral')
axes[1].axhline(y=0, color='red', linestyle='--', lw=2)
axes[1].set_xlabel('Predicted Bookings', fontsize=12, fontweight='bold')
axes[1].set_ylabel('Residuals (Actual - Predicted)', fontsize=12, fontweight='bold')
axes[1].set_title('Residual Plot (Test Set)', fontsize=14, fontweight='bold')
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('visualizations/v5_predictions.png', dpi=150, bbox_inches='tight')
print("  [OK] Saved: visualizations/v5_predictions.png")

# 3. Model comparison report
print("\n[GENERATING COMPARISON REPORT]")
with open('MODEL_V5_REPORT.txt', 'w') as f:
    f.write("="*80 + "\n")
    f.write("MODEL V5: BUSINESS-FOCUSED DEMAND FORECASTING\n")
    f.write("="*80 + "\n")
    f.write(f"Training Date: {datetime.now()}\n")
    f.write(f"Model Type: XGBoost Regressor\n")
    f.write(f"Target: 2-Day Ahead Demand Prediction\n\n")
    
    f.write("KEY IMPROVEMENTS OVER V4:\n")
    f.write("  1. Removed branch/city identifiers (now using size buckets)\n")
    f.write("  2. Added comprehensive price elasticity features\n")
    f.write("  3. Added lag features (1d, 2d, 3d, 7d, 14d, 21d, 30d)\n")
    f.write("  4. Enhanced seasonality with more Fourier components\n")
    f.write("  5. Focus on ACTIONABLE features for pricing decisions\n\n")
    
    f.write("PERFORMANCE METRICS:\n")
    f.write(f"  Test R²:       {test_metrics['r2']:.4f}\n")
    f.write(f"  Test RMSE:     {test_metrics['rmse']:.2f}\n")
    f.write(f"  Test MAE:      {test_metrics['mae']:.2f}\n")
    f.write(f"  Test MAPE:     {test_metrics['mape']*100:.2f}%\n\n")
    
    f.write("OVERFITTING CHECK:\n")
    f.write(f"  Train-Test R² Gap: {r2_gap:.4f}\n")
    f.write(f"  Status: {'ROBUST' if r2_gap < 0.1 else 'NEEDS REVIEW'}\n\n")
    
    f.write("FEATURE IMPORTANCE BY CATEGORY:\n")
    for cat, imp in category_importance.items():
        f.write(f"  {cat:30} {imp:.4f}\n")
    
    f.write("\nTOP 20 FEATURES:\n")
    for _, row in feature_importance.head(20).iterrows():
        f.write(f"  {row['Feature']:40} {row['Importance']:.4f}\n")
    
    f.write("\n" + "="*80 + "\n")

print("  [OK] Saved: MODEL_V5_REPORT.txt")

print("\n" + "="*100)
print("MODEL V5 TRAINING COMPLETE!")
print("="*100)
print(f"Completed at: {datetime.now()}")
print("="*100)

