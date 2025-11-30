"""
Compare Pricing Modes: Multiplicative vs Hierarchical

This script demonstrates the difference between the two pricing strategies
by running the same scenarios through both modes.
"""

import config
from pricing_rules import PricingRules
from datetime import datetime
import pandas as pd

def compare_scenarios():
    """Compare how both modes handle different scenarios."""
    
    print("=" * 100)
    print("PRICING MODE COMPARISON: Multiplicative vs Hierarchical")
    print("=" * 100)
    
    # Initialize pricing rules
    pricing = PricingRules(min_multiplier=0.80, max_multiplier=2.50)
    
    # Scenarios to test
    scenarios = [
        {
            'name': 'Low Demand + High Utilization (Your Case)',
            'base_price': 200,
            'predicted_demand': 60,
            'average_demand': 100,
            'available_vehicles': 367,
            'total_vehicles': 2277,
            'is_holiday': False,
            'is_weekend': False,
        },
        {
            'name': 'High Demand + High Utilization',
            'base_price': 200,
            'predicted_demand': 150,
            'average_demand': 100,
            'available_vehicles': 200,
            'total_vehicles': 1000,
            'is_holiday': False,
            'is_weekend': False,
        },
        {
            'name': 'Low Demand + Low Utilization',
            'base_price': 200,
            'predicted_demand': 60,
            'average_demand': 100,
            'available_vehicles': 800,
            'total_vehicles': 1000,
            'is_holiday': False,
            'is_weekend': False,
        },
        {
            'name': 'High Demand + Low Utilization',
            'base_price': 200,
            'predicted_demand': 150,
            'average_demand': 100,
            'available_vehicles': 800,
            'total_vehicles': 1000,
            'is_holiday': False,
            'is_weekend': False,
        },
        {
            'name': 'Holiday + High Demand + Low Availability',
            'base_price': 200,
            'predicted_demand': 160,
            'average_demand': 100,
            'available_vehicles': 100,
            'total_vehicles': 1000,
            'is_holiday': True,
            'is_weekend': True,
        },
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"\n{'=' * 100}")
        print(f"SCENARIO: {scenario['name']}")
        print(f"{'=' * 100}")
        
        # Calculate utilization
        utilization_pct = ((scenario['total_vehicles'] - scenario['available_vehicles']) / 
                          scenario['total_vehicles'] * 100)
        
        print(f"\nInputs:")
        print(f"  Base Price:         {scenario['base_price']} SAR")
        print(f"  Predicted Demand:   {scenario['predicted_demand']} (avg: {scenario['average_demand']})")
        print(f"  Demand Ratio:       {scenario['predicted_demand']/scenario['average_demand']:.2f}x")
        print(f"  Utilization:        {utilization_pct:.1f}% ({scenario['total_vehicles']-scenario['available_vehicles']}/{scenario['total_vehicles']} rented)")
        print(f"  Available:          {scenario['available_vehicles']} vehicles")
        if scenario['is_holiday']:
            print(f"  Holiday:            Yes")
        if scenario['is_weekend']:
            print(f"  Weekend:            Yes")
        
        # Test MULTIPLICATIVE mode
        original_mode = config.PRICING_MODE
        config.PRICING_MODE = 'multiplicative'
        
        # Remove 'name' from scenario for function call
        scenario_params = {k: v for k, v in scenario.items() if k != 'name'}
        result_mult = pricing.calculate_final_price(**scenario_params)
        
        print(f"\n{'-' * 50}")
        print(f"MULTIPLICATIVE MODE (Legacy):")
        print(f"{'-' * 50}")
        print(f"  Demand Multiplier:  {result_mult['demand_multiplier']:.2f}x")
        print(f"  Supply Multiplier:  {result_mult['supply_multiplier']:.2f}x")
        print(f"  Event Multiplier:   {result_mult['event_multiplier']:.2f}x")
        print(f"  Combined:           {result_mult['demand_multiplier']} x {result_mult['supply_multiplier']} x {result_mult['event_multiplier']} = {result_mult['combined_multiplier']:.4f}")
        print(f"  Final Price:        {result_mult['final_price']} SAR ({result_mult['price_change_pct']:+.1f}%)")
        
        # Test HIERARCHICAL mode
        config.PRICING_MODE = 'hierarchical'
        
        result_hier = pricing.calculate_final_price(**scenario_params)
        
        print(f"\n{'-' * 50}")
        print(f"HIERARCHICAL MODE (Best Practice):")
        print(f"{'-' * 50}")
        print(f"  Demand Multiplier:  {result_hier['demand_multiplier']:.2f}x (PRIMARY)")
        print(f"  Supply Multiplier:  {result_hier['supply_multiplier']:.2f}x (SECONDARY)")
        print(f"  Event Multiplier:   {result_hier['event_multiplier']:.2f}x (stacks with demand)")
        print(f"  Mode Logic:         {result_hier['mode_explanation']}")
        print(f"  Final Price:        {result_hier['final_price']} SAR ({result_hier['price_change_pct']:+.1f}%)")
        
        # Compare
        price_diff = result_hier['final_price'] - result_mult['final_price']
        pct_diff = result_hier['price_change_pct'] - result_mult['price_change_pct']
        
        print(f"\n{'-' * 50}")
        print(f"DIFFERENCE:")
        print(f"{'-' * 50}")
        print(f"  Price Difference:   {price_diff:+.2f} SAR")
        print(f"  Percent Difference: {pct_diff:+.1f} percentage points")
        
        if abs(price_diff) < 1:
            print(f"  Impact:             Minimal difference")
        elif price_diff > 0:
            print(f"  Impact:             Hierarchical is MORE EXPENSIVE (better for revenue)")
        else:
            print(f"  Impact:             Hierarchical is CHEAPER (better for bookings)")
        
        # Store for summary
        results.append({
            'Scenario': scenario['name'],
            'Utilization': f"{utilization_pct:.1f}%",
            'Demand': f"{scenario['predicted_demand']/scenario['average_demand']:.2f}x",
            'Mult_Price': f"{result_mult['final_price']:.0f} SAR",
            'Mult_Change': f"{result_mult['price_change_pct']:+.1f}%",
            'Hier_Price': f"{result_hier['final_price']:.0f} SAR",
            'Hier_Change': f"{result_hier['price_change_pct']:+.1f}%",
            'Difference': f"{price_diff:+.2f} SAR",
        })
        
        # Restore original mode
        config.PRICING_MODE = original_mode
    
    # Summary table
    print(f"\n\n{'=' * 100}")
    print("SUMMARY COMPARISON TABLE")
    print(f"{'=' * 100}\n")
    
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    
    print(f"\n{'=' * 100}")
    print("KEY INSIGHTS:")
    print(f"{'=' * 100}")
    print("""
1. MULTIPLICATIVE (Legacy):
   - All factors multiply together equally
   - Can result in "cancellation" (e.g., 0.85 x 1.15 = 0.98)
   - Balanced approach but not optimized for revenue management

2. HIERARCHICAL (Best Practice):
   - Demand is PRIMARY driver (most accurate predictor)
   - Utilization is SECONDARY (constrains discounts, accelerates premiums)
   - Follows Emirates/Booking.com/Hertz standards
   - Better aligned with consultant recommendations

3. When They Differ Most:
   - Low demand + High utilization -> Hierarchical limits discount more
   - High demand + High utilization -> Hierarchical amplifies premium more
   - Both modes are similar when demand = average (neutral)

RECOMMENDATION: Use HIERARCHICAL mode for production.
To switch: Change PRICING_MODE in config.py
""")
    
    print(f"{'=' * 100}\n")


if __name__ == "__main__":
    compare_scenarios()

