"""
HYBRID PRICING ENGINE: V4 (Baseline) + V5 (Elasticity)
========================================================

Two-Stage Architecture:
1. Stage 1 (V4): Predict baseline demand (structural features only)
2. Stage 2 (V5): Predict price elasticity (how demand responds to price changes)
3. Combine: final_demand = baseline_demand * elasticity_factor

This gives us:
- V4's high accuracy (96.57% R²) for baseline forecasting
- V5's price sensitivity for pricing decisions
- Best of both worlds
"""

import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class HybridPricingEngine:
    """
    Combines V4 (baseline demand) and V5 (price elasticity) models
    for accurate demand forecasting with price sensitivity
    """
    
    def __init__(self):
        """Load both models"""
        print("="*80)
        print("HYBRID PRICING ENGINE INITIALIZATION")
        print("="*80)
        
        # Load V4 (baseline demand model)
        try:
            with open('models/demand_prediction_ROBUST_v4.pkl', 'rb') as f:
                self.model_v4_baseline = pickle.load(f)
            with open('models/feature_columns_ROBUST_v4.pkl', 'rb') as f:
                self.features_v4 = pickle.load(f)
            print("[OK] V4 Baseline Model loaded (R2 = 96.57%)")
        except Exception as e:
            print(f"[FAIL] Failed to load V4: {e}")
            self.model_v4_baseline = None
            
        # Load V5 (price elasticity model)
        try:
            with open('models/demand_prediction_v5_business.pkl', 'rb') as f:
                self.model_v5_elasticity = pickle.load(f)
            with open('models/feature_columns_v5.pkl', 'rb') as f:
                self.features_v5 = pickle.load(f)
            print("[OK] V5 Elasticity Model loaded (62% price features)")
        except Exception as e:
            print(f"[FAIL] Failed to load V5: {e}")
            self.model_v5_elasticity = None
            
        # Load historical data for reference
        try:
            self.historical_data = pd.read_parquet('data/processed/training_data.parquet')
            print(f"[OK] Historical data loaded ({len(self.historical_data):,} records)")
        except Exception as e:
            print(f"[FAIL] Failed to load historical data: {e}")
            self.historical_data = None
            
        print("="*80 + "\n")
    
    def predict_baseline_demand(self, 
                               branch_id: int,
                               category_id: int,
                               date: datetime,
                               **kwargs) -> float:
        """
        Stage 1: Predict baseline demand using V4 (structural features only)
        
        This tells us: "What demand to expect at typical/average pricing"
        """
        if self.model_v4_baseline is None:
            raise ValueError("V4 model not loaded")
        
        # Prepare features for V4 (no price features)
        features_v4_dict = self._prepare_v4_features(
            branch_id=branch_id,
            category_id=category_id,
            date=date,
            **kwargs
        )
        
        # Create feature vector
        X = pd.DataFrame([features_v4_dict])[self.features_v4]
        
        # Predict
        baseline_demand = self.model_v4_baseline.predict(X)[0]
        
        return max(0, baseline_demand)  # Ensure non-negative
    
    def predict_price_elasticity(self,
                                 current_price: float,
                                 branch_id: int,
                                 category_id: int,
                                 date: datetime,
                                 historical_demand: float = None,
                                 **kwargs) -> float:
        """
        Stage 2: Predict elasticity factor using V5 (price-focused features)
        
        Returns: multiplier (e.g., 1.0 = no change, 0.9 = 10% decrease, 1.1 = 10% increase)
        """
        if self.model_v5_elasticity is None:
            return 1.0  # Neutral if V5 not available
        
        # Prepare features for V5 (with price features)
        features_v5_dict = self._prepare_v5_features(
            current_price=current_price,
            branch_id=branch_id,
            category_id=category_id,
            date=date,
            historical_demand=historical_demand,
            **kwargs
        )
        
        # Create feature vector
        X = pd.DataFrame([features_v5_dict])[self.features_v5]
        
        # Predict demand with price
        demand_with_price = self.model_v5_elasticity.predict(X)[0]
        
        # Get reference demand (at average historical price)
        avg_price = self._get_historical_avg_price(branch_id, category_id)
        reference_features = features_v5_dict.copy()
        reference_features['AvgPrice'] = avg_price
        X_ref = pd.DataFrame([reference_features])[self.features_v5]
        reference_demand = self.model_v5_elasticity.predict(X_ref)[0]
        
        # Calculate elasticity factor
        if reference_demand > 0:
            elasticity_factor = demand_with_price / reference_demand
        else:
            elasticity_factor = 1.0
        
        # Bound the elasticity (prevent extreme values)
        elasticity_factor = np.clip(elasticity_factor, 0.5, 2.0)
        
        return elasticity_factor
    
    def predict_demand(self,
                      current_price: float,
                      branch_id: int,
                      category_id: int,
                      date: datetime,
                      **kwargs) -> Dict:
        """
        Combined prediction: baseline * elasticity
        
        Returns:
        {
            'final_demand': float,
            'baseline_demand': float,
            'elasticity_factor': float,
            'confidence': str,
            'explanation': str
        }
        """
        # Stage 1: Baseline demand
        baseline_demand = self.predict_baseline_demand(
            branch_id=branch_id,
            category_id=category_id,
            date=date,
            **kwargs
        )
        
        # Stage 2: Elasticity factor
        elasticity_factor = self.predict_price_elasticity(
            current_price=current_price,
            branch_id=branch_id,
            category_id=category_id,
            date=date,
            historical_demand=baseline_demand,
            **kwargs
        )
        
        # Combine
        final_demand = baseline_demand * elasticity_factor
        
        # Determine confidence
        if self.model_v4_baseline and self.model_v5_elasticity:
            confidence = "High"
        elif self.model_v4_baseline:
            confidence = "Medium (baseline only)"
        else:
            confidence = "Low"
        
        # Generate explanation
        if elasticity_factor > 1.05:
            price_effect = f"Price below average (+{(elasticity_factor-1)*100:.1f}% demand boost)"
        elif elasticity_factor < 0.95:
            price_effect = f"Price above average ({(elasticity_factor-1)*100:.1f}% demand reduction)"
        else:
            price_effect = "Price near average (minimal impact)"
        
        explanation = (
            f"Baseline demand: {baseline_demand:.1f} bookings. "
            f"{price_effect}. "
            f"Final estimate: {final_demand:.1f} bookings."
        )
        
        return {
            'final_demand': round(final_demand, 1),
            'baseline_demand': round(baseline_demand, 1),
            'elasticity_factor': round(elasticity_factor, 3),
            'confidence': confidence,
            'explanation': explanation,
            'model_v4_used': self.model_v4_baseline is not None,
            'model_v5_used': self.model_v5_elasticity is not None
        }
    
    def price_optimizer(self,
                       branch_id: int,
                       category_id: int,
                       date: datetime,
                       price_range: Tuple[float, float],
                       n_prices: int = 10,
                       **kwargs) -> pd.DataFrame:
        """
        Test multiple prices and find optimal revenue point
        
        Returns DataFrame with columns:
        - price
        - predicted_demand
        - expected_revenue
        - elasticity_factor
        """
        min_price, max_price = price_range
        prices = np.linspace(min_price, max_price, n_prices)
        
        results = []
        for price in prices:
            prediction = self.predict_demand(
                current_price=price,
                branch_id=branch_id,
                category_id=category_id,
                date=date,
                **kwargs
            )
            
            results.append({
                'price': price,
                'predicted_demand': prediction['final_demand'],
                'expected_revenue': price * prediction['final_demand'],
                'baseline_demand': prediction['baseline_demand'],
                'elasticity_factor': prediction['elasticity_factor']
            })
        
        df_results = pd.DataFrame(results)
        
        # Find optimal price (max revenue)
        optimal_idx = df_results['expected_revenue'].idxmax()
        df_results['is_optimal'] = False
        df_results.loc[optimal_idx, 'is_optimal'] = True
        
        return df_results
    
    def _prepare_v4_features(self, branch_id, category_id, date, **kwargs):
        """Prepare features for V4 (baseline model)"""
        # This is simplified - in production, you'd load full feature engineering
        # from the training pipeline
        
        features = {
            'PickupBranchId': branch_id,
            'CategoryId': category_id,
            'DayOfWeek': date.weekday(),
            'Month': date.month,
            'Quarter': (date.month - 1) // 3 + 1,
            'IsWeekend': 1 if date.weekday() >= 5 else 0,
            'DayOfYear': date.timetuple().tm_yday,
            # Add more features as needed
        }
        
        # Fill remaining features with defaults
        for feat in self.features_v4:
            if feat not in features:
                features[feat] = 0
        
        return features
    
    def _prepare_v5_features(self, current_price, branch_id, category_id, date, 
                             historical_demand=None, **kwargs):
        """Prepare features for V5 (elasticity model)"""
        # This is simplified - in production, you'd compute lags, rolling stats, etc.
        
        features = {
            'AvgPrice': current_price,
            'StdPrice': 0,  # Would compute from recent data
            'DayOfWeek': date.weekday(),
            'Month': date.month,
            'IsWeekend': 1 if date.weekday() >= 5 else 0,
            'DayOfYear': date.timetuple().tm_yday,
            # Add price change features
            'Price_Change_1d': 0,
            'Price_Change_7d': 0,
            'Price_Change_Pct_1d': 0,
            'Price_Change_Pct_7d': 0,
            # Add lag features if available
            'Demand_Lag_7d': historical_demand if historical_demand else 0,
        }
        
        # Fill remaining features with defaults
        for feat in self.features_v5:
            if feat not in features:
                features[feat] = 0
        
        return features
    
    def _get_historical_avg_price(self, branch_id, category_id):
        """Get historical average price for branch-category"""
        if self.historical_data is not None:
            mask = (
                (self.historical_data['PickupBranchId'] == branch_id) &
                (self.historical_data['VehicleId'] == category_id)
            )
            avg_price = self.historical_data.loc[mask, 'DailyRateAmount'].mean()
            return avg_price if not pd.isna(avg_price) else 300.0
        return 300.0  # Default


def demo_hybrid_engine():
    """Demo the hybrid engine with example scenarios"""
    print("\n" + "="*80)
    print("HYBRID ENGINE DEMO: Real-World Scenarios")
    print("="*80 + "\n")
    
    engine = HybridPricingEngine()
    
    # Scenario 1: Normal weekday pricing
    print("\n[SCENARIO 1]: Normal Weekday - Economy Car at Riyadh Airport")
    print("-"*80)
    
    result = engine.predict_demand(
        current_price=250,
        branch_id=5,
        category_id=10,
        date=datetime(2025, 12, 10)  # Wednesday
    )
    
    print(f"  Price: 250 SAR")
    print(f"  Baseline Demand: {result['baseline_demand']:.1f} bookings")
    print(f"  Elasticity Factor: {result['elasticity_factor']:.3f}")
    print(f"  Final Demand: {result['final_demand']:.1f} bookings")
    print(f"  Explanation: {result['explanation']}")
    
    # Scenario 2: Test different prices
    print("\n\n[SCENARIO 2]: Price Optimization (200-400 SAR range)")
    print("-"*80)
    
    df_prices = engine.price_optimizer(
        branch_id=5,
        category_id=10,
        date=datetime(2025, 12, 10),
        price_range=(200, 400),
        n_prices=9
    )
    
    print("\n  Price Testing Results:")
    print(df_prices[['price', 'predicted_demand', 'expected_revenue', 'elasticity_factor']].to_string(index=False))
    
    optimal = df_prices[df_prices['is_optimal']].iloc[0]
    print(f"\n  [OPTIMAL PRICE]: {optimal['price']:.0f} SAR")
    print(f"     Expected Demand: {optimal['predicted_demand']:.1f} bookings")
    print(f"     Expected Revenue: {optimal['expected_revenue']:.0f} SAR")
    
    # Scenario 3: High vs Low price comparison
    print("\n\n[SCENARIO 3]: Compare Low (200 SAR) vs High (400 SAR) Pricing")
    print("-"*80)
    
    low_price = engine.predict_demand(current_price=200, branch_id=5, category_id=10, date=datetime(2025, 12, 10))
    high_price = engine.predict_demand(current_price=400, branch_id=5, category_id=10, date=datetime(2025, 12, 10))
    
    print(f"\n  [LOW PRICE (200 SAR)]:")
    print(f"     Demand: {low_price['final_demand']:.1f} bookings")
    print(f"     Revenue: {200 * low_price['final_demand']:.0f} SAR")
    print(f"     Elasticity: {low_price['elasticity_factor']:.3f}")
    
    print(f"\n  [HIGH PRICE (400 SAR)]:")
    print(f"     Demand: {high_price['final_demand']:.1f} bookings")
    print(f"     Revenue: {400 * high_price['final_demand']:.0f} SAR")
    print(f"     Elasticity: {high_price['elasticity_factor']:.3f}")
    
    revenue_diff = (400 * high_price['final_demand']) - (200 * low_price['final_demand'])
    print(f"\n  [Revenue Difference]: {revenue_diff:+.0f} SAR")
    
    if revenue_diff > 0:
        print(f"     [OK] Higher price generates {revenue_diff:.0f} SAR more revenue despite lower demand")
    else:
        print(f"     [OK] Lower price generates {abs(revenue_diff):.0f} SAR more revenue through volume")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    demo_hybrid_engine()

