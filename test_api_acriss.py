"""
Test Booking.com API response to check for ACRISS codes
and see all available vehicle fields
"""
import requests
import json
from datetime import datetime, timedelta

API_KEY = "2d4ad88e62mshfb8fb27c0b4e2f8p1fbb48jsn854faa573903"
API_HOST = "booking-com.p.rapidapi.com"

def test_api_raw_response():
    """Get raw API response to check for ACRISS codes"""
    
    url = f"https://{API_HOST}/v1/car-rental/search"
    
    headers = {
        "x-rapidapi-host": API_HOST,
        "x-rapidapi-key": API_KEY
    }
    
    # Riyadh Airport coordinates
    pick_up = datetime.now() + timedelta(days=1)
    drop_off = pick_up + timedelta(days=2)
    
    params = {
        "pick_up_latitude": 24.9576,
        "pick_up_longitude": 46.6987,
        "drop_off_latitude": 24.9576,
        "drop_off_longitude": 46.6987,
        "pick_up_datetime": pick_up.strftime("%Y-%m-%d 10:00:00"),
        "drop_off_datetime": drop_off.strftime("%Y-%m-%d 10:00:00"),
        "currency": "SAR",
        "locale": "en-gb",
        "from_country": "ar",
        "sort_by": "recommended"
    }
    
    print("="*80)
    print("TESTING BOOKING.COM API - CHECKING FOR ACRISS CODES")
    print("="*80)
    print(f"Pick-up: {params['pick_up_datetime']}")
    print(f"Drop-off: {params['drop_off_datetime']}")
    print()
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    
    if response.status_code != 200:
        print(f"ERROR: API returned {response.status_code}")
        print(response.text[:500])
        return
    
    data = response.json()
    
    if 'search_results' not in data:
        print("ERROR: No search_results in response")
        print(json.dumps(data, indent=2)[:1000])
        return
    
    results = data['search_results']
    print(f"Found {len(results)} car rental options\n")
    
    # Check first 5 cars for all available fields
    print("="*80)
    print("SAMPLE CAR DATA (checking for ACRISS codes):")
    print("="*80)
    
    all_vehicle_fields = set()
    acriss_found = False
    
    for i, car in enumerate(results[:5]):
        print(f"\n--- Car {i+1} ---")
        
        vehicle_info = car.get('vehicle_info', {})
        
        # Print all vehicle_info fields
        print("vehicle_info fields:")
        for key, value in vehicle_info.items():
            print(f"  {key}: {value}")
            all_vehicle_fields.add(key)
            
            # Check if this looks like an ACRISS code
            if isinstance(value, str) and len(value) == 4 and value.isupper():
                print(f"    ^ POSSIBLE ACRISS CODE!")
                acriss_found = True
        
        # Check other sections for ACRISS
        for section in ['pricing_info', 'supplier_info', 'rate_info']:
            section_data = car.get(section, {})
            for key, value in section_data.items():
                if 'acriss' in key.lower() or 'sipp' in key.lower():
                    print(f"  {section}.{key}: {value}")
                    acriss_found = True
    
    print("\n" + "="*80)
    print("SUMMARY OF ALL VEHICLE FIELDS:")
    print("="*80)
    for field in sorted(all_vehicle_fields):
        print(f"  - {field}")
    
    if acriss_found:
        print("\n✓ ACRISS/SIPP CODES FOUND IN API RESPONSE!")
    else:
        print("\n✗ NO ACRISS/SIPP CODES FOUND IN API RESPONSE")
        print("  The API provides category through 'group' field (e.g., 'Economy', 'Compact')")
    
    # Save sample response for analysis
    sample_output = {
        "sample_cars": results[:3],
        "all_vehicle_fields": list(all_vehicle_fields)
    }
    
    with open("data/sample_api_response.json", 'w') as f:
        json.dump(sample_output, f, indent=2)
    print(f"\n✓ Sample saved to data/sample_api_response.json")

if __name__ == "__main__":
    test_api_raw_response()

