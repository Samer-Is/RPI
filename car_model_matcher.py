"""
Car Model Matcher
Matches specific car models between Renty fleet and competitor data
to enable car-by-car price comparison
"""
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import re

# Renty fleet car models (based on categories shown in dashboard)
RENTY_FLEET = {
    "Economy": [
        {"model": "Hyundai Accent", "brand": "Hyundai"},
        {"model": "Kia Picanto", "brand": "Kia"},
        {"model": "Nissan Sunny", "brand": "Nissan"},
        {"model": "Chevrolet Spark", "brand": "Chevrolet"},
        {"model": "Hyundai i10", "brand": "Hyundai"},
    ],
    "Compact": [
        {"model": "Toyota Yaris", "brand": "Toyota"},
        {"model": "Hyundai Elantra", "brand": "Hyundai"},
        {"model": "Kia Cerato", "brand": "Kia"},
        {"model": "Kia Pegas", "brand": "Kia"},
        {"model": "Nissan Sunny", "brand": "Nissan"},
    ],
    "Standard": [
        {"model": "Toyota Camry", "brand": "Toyota"},
        {"model": "Hyundai Sonata", "brand": "Hyundai"},
        {"model": "Nissan Altima", "brand": "Nissan"},
        {"model": "Toyota Corolla", "brand": "Toyota"},
        {"model": "Chevrolet Malibu", "brand": "Chevrolet"},
    ],
    "SUV Compact": [
        {"model": "Hyundai Tucson", "brand": "Hyundai"},
        {"model": "Nissan Qashqai", "brand": "Nissan"},
        {"model": "Kia Sportage", "brand": "Kia"},
        {"model": "Hyundai Creta", "brand": "Hyundai"},
        {"model": "Hyundai Kona", "brand": "Hyundai"},
    ],
    "SUV Standard": [
        {"model": "Toyota RAV4", "brand": "Toyota"},
        {"model": "Nissan X-Trail", "brand": "Nissan"},
        {"model": "Hyundai Santa Fe", "brand": "Hyundai"},
        {"model": "Toyota Fortuner", "brand": "Toyota"},
    ],
    "SUV Large": [
        {"model": "Toyota Land Cruiser", "brand": "Toyota"},
        {"model": "Nissan Patrol", "brand": "Nissan"},
        {"model": "Chevrolet Tahoe", "brand": "Chevrolet"},
        {"model": "Toyota Highlander", "brand": "Toyota"},
    ],
    "Luxury Sedan": [
        {"model": "BMW 5 Series", "brand": "BMW"},
        {"model": "Mercedes E-Class", "brand": "Mercedes"},
        {"model": "Audi A6", "brand": "Audi"},
        {"model": "Chrysler 300C", "brand": "Chrysler"},
    ],
    "Luxury SUV": [
        {"model": "BMW X5", "brand": "BMW"},
        {"model": "Mercedes GLE", "brand": "Mercedes"},
        {"model": "Audi Q7", "brand": "Audi"},
        {"model": "Range Rover", "brand": "Range Rover"},
    ],
}


def normalize_model_name(name: str) -> str:
    """Normalize vehicle model name for comparison"""
    # Remove extra whitespace
    name = ' '.join(name.strip().split())
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove common suffixes
    suffixes = [' gps', ' sedan', ' hatchback', ' suv', ' or similar']
    for suffix in suffixes:
        name = name.replace(suffix, '')
    
    return name.strip()


def extract_brand_model(vehicle_name: str) -> Tuple[str, str]:
    """Extract brand and model from vehicle name"""
    parts = vehicle_name.strip().split()
    if len(parts) >= 2:
        brand = parts[0]
        model = ' '.join(parts[1:])
        return brand, model
    return vehicle_name, vehicle_name


def calculate_similarity(s1: str, s2: str) -> float:
    """Calculate string similarity score (0-1)"""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def find_matching_vehicles(competitor_data: Dict, renty_base_prices: Dict) -> List[Dict]:
    """
    Find competitor vehicles that match Renty fleet vehicles
    
    Args:
        competitor_data: Dict with category -> competitors list from stored data
        renty_base_prices: Dict with category -> base_price
    
    Returns:
        List of matched vehicles with comparison data
    """
    matches = []
    
    # Flatten all competitor vehicles
    competitor_vehicles = []
    for category, data in competitor_data.items():
        if isinstance(data, dict) and 'competitors' in data:
            for comp in data.get('competitors', []):
                competitor_vehicles.append({
                    'vehicle': comp.get('Vehicle', ''),
                    'supplier': comp.get('Competitor_Name', ''),
                    'price': comp.get('Competitor_Price', 0),
                    'category': category
                })
    
    # For each Renty model, find matching competitor vehicles
    for renty_category, models in RENTY_FLEET.items():
        base_price = renty_base_prices.get(renty_category, 0)
        
        for renty_model in models:
            renty_name = renty_model['model']
            renty_name_normalized = normalize_model_name(renty_name)
            
            # Find matching competitor vehicles
            for comp_vehicle in competitor_vehicles:
                comp_name = comp_vehicle['vehicle']
                comp_name_normalized = normalize_model_name(comp_name)
                
                # Calculate similarity
                similarity = calculate_similarity(renty_name_normalized, comp_name_normalized)
                
                # Check for exact model match (brand + model)
                renty_brand, renty_model_only = extract_brand_model(renty_name)
                comp_brand, comp_model_only = extract_brand_model(comp_name)
                
                # High match threshold
                is_match = False
                match_type = None
                
                # Exact match
                if renty_name_normalized == comp_name_normalized:
                    is_match = True
                    match_type = "exact"
                # Model contains the other
                elif renty_name_normalized in comp_name_normalized or comp_name_normalized in renty_name_normalized:
                    is_match = True
                    match_type = "contains"
                # Same brand and model starts with same word
                elif (renty_brand.lower() == comp_brand.lower() and 
                      renty_model_only.split()[0].lower() == comp_model_only.split()[0].lower()):
                    is_match = True
                    match_type = "brand_model"
                # High similarity
                elif similarity >= 0.8:
                    is_match = True
                    match_type = f"similarity_{similarity:.0%}"
                
                if is_match:
                    price_diff = base_price - comp_vehicle['price'] if base_price > 0 else 0
                    price_diff_pct = (price_diff / comp_vehicle['price'] * 100) if comp_vehicle['price'] > 0 else 0
                    
                    matches.append({
                        'renty_model': renty_name,
                        'renty_category': renty_category,
                        'renty_base_price': base_price,
                        'competitor_model': comp_vehicle['vehicle'],
                        'competitor_supplier': comp_vehicle['supplier'],
                        'competitor_price': comp_vehicle['price'],
                        'competitor_category': comp_vehicle['category'],
                        'match_type': match_type,
                        'price_difference': round(price_diff, 2),
                        'price_difference_pct': round(price_diff_pct, 1),
                        'is_cheaper': price_diff > 0
                    })
    
    # Remove duplicates (same Renty model + same competitor)
    seen = set()
    unique_matches = []
    for m in matches:
        key = (m['renty_model'], m['competitor_model'], m['competitor_supplier'])
        if key not in seen:
            seen.add(key)
            unique_matches.append(m)
    
    # Sort by Renty model name
    unique_matches.sort(key=lambda x: (x['renty_category'], x['renty_model']))
    
    return unique_matches


def get_best_matches_per_model(matches: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group matches by Renty model and return best matches
    
    Returns dict: renty_model -> list of competitor matches (best price per supplier)
    """
    model_matches = {}
    
    for match in matches:
        renty_model = match['renty_model']
        if renty_model not in model_matches:
            model_matches[renty_model] = []
        model_matches[renty_model].append(match)
    
    # For each model, keep only the best price per supplier
    for model, model_data in model_matches.items():
        supplier_best = {}
        for m in model_data:
            supplier = m['competitor_supplier']
            if supplier not in supplier_best or m['competitor_price'] < supplier_best[supplier]['competitor_price']:
                supplier_best[supplier] = m
        model_matches[model] = sorted(supplier_best.values(), key=lambda x: x['competitor_price'])
    
    return model_matches


# Test function
if __name__ == "__main__":
    import json
    
    # Load stored competitor data
    with open('data/competitor_prices/daily_competitor_prices.json', 'r') as f:
        data = json.load(f)
    
    # Get first branch data
    branch_name = list(data['branches'].keys())[0]
    branch_data = data['branches'][branch_name]['categories']
    
    # Sample base prices
    base_prices = {
        "Economy": 102,
        "Compact": 143,
        "Standard": 188,
        "SUV Compact": 204,
        "SUV Standard": 224,
        "SUV Large": 317,
        "Luxury Sedan": 515,
        "Luxury SUV": 893
    }
    
    # Find matches
    matches = find_matching_vehicles(branch_data, base_prices)
    
    print(f"\nFound {len(matches)} model matches for {branch_name}\n")
    print("="*80)
    
    for match in matches[:10]:
        status = "CHEAPER" if match['is_cheaper'] else "MORE EXPENSIVE"
        print(f"Renty: {match['renty_model']:20} ({match['renty_category']})")
        print(f"  vs {match['competitor_supplier']}: {match['competitor_model']}")
        print(f"  Renty: {match['renty_base_price']} SAR vs Competitor: {match['competitor_price']} SAR")
        print(f"  -> {status} by {abs(match['price_difference'])} SAR ({abs(match['price_difference_pct']):.1f}%)")
        print()

