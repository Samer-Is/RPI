"""
Test scraper with different branches and categories to verify mapping
"""
from competitor_scraper import get_competitor_prices_for_dashboard
from datetime import datetime

# Test cases: different branches and categories
test_cases = [
    {"branch": "King Khalid Airport - Riyadh", "category": "Economy"},
    {"branch": "King Abdulaziz Airport - Jeddah", "category": "SUV Standard"},
    {"branch": "Al Khobar Business District", "category": "Luxury Sedan"},
    {"branch": "Mecca City Center", "category": "Standard"},
]

print("="*80)
print("COMPETITOR SCRAPER - LOCATION & CATEGORY MAPPING TEST")
print("="*80)

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}/{len(test_cases)}")
    print(f"Branch: {test['branch']}")
    print(f"Category: {test['category']}")
    print("-" * 80)
    
    try:
        result = get_competitor_prices_for_dashboard(
            category=test['category'],
            branch_name=test['branch'],
            date=datetime.now()
        )
        
        if result.get('competitors'):
            print(f"[OK] Found {len(result['competitors'])} competitors")
            print(f"  Location: {result['competitors'][0].get('Location', 'N/A')}")
            print(f"  Average Price: {result['avg_price']:.2f} SAR")
            print(f"  Data Source: {result['data_source']}")
            
            # Show top 3 results
            for j, comp in enumerate(result['competitors'][:3], 1):
                print(f"  {j}. {comp['Competitor_Name']}: {comp['Competitor_Price']} SAR "
                      f"({comp['Competitor_Category']}, {comp['Confidence']}% confidence)")
        else:
            print("[WARN] No results found")
            
    except Exception as e:
        print(f"[ERROR] {e}")
    
    print()

print("="*80)
print("Test Complete")
print("="*80)

