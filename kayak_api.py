"""
Kayak Search API Integration for Car Rentals
Fetches real competitor pricing from Kayak aggregator
"""
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from car_model_category_mapping import get_correct_category
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KayakAPI:
    """
    Kayak Search API client for car rental pricing
    """
    
    def __init__(self):
        self.api_key = "2d4ad88e62mshfb8fb27c0b4e2f8p1fbb48jsn854faa573903"
        self.host = "kayak-search.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-host": self.host,
            "x-rapidapi-key": self.api_key
        }
        
        # Kayak location IDs for Renty branches
        self.location_mapping = {
            "King Khalid Airport - Riyadh": "RUH::airport",
            "Olaya District - Riyadh": "35744::city",
            "King Abdulaziz Airport - Jeddah": "JED::airport",
            "Jeddah City Center": "17976::city",  # Fixed: was 21838
            "King Fahd Airport - Dammam": "DMM::airport",
            "Al Khobar Business District": "33765::city",  # Fixed: was 39553
            "Mecca City Center": "7523::city",  # Fixed: was 21852
            "Medina Downtown": "45635::city"  # Fixed: was 21857
        }
        
        # Kayak categories to Renty categories mapping
        self.category_mapping = {
            "Economy": ["Mini", "Economy"],
            "Compact": ["Compact"],
            "Standard": ["Intermediate", "Standard", "Full-size", "Medium"],
            "SUV Compact": ["Compact SUV", "Small SUV"],
            "SUV Standard": ["Standard SUV", "Medium SUV", "SUV"],
            "SUV Large": ["Large SUV", "Full-size SUV", "Premium SUV"],
            "Luxury Sedan": ["Luxury", "Premium"],
            "Luxury SUV": ["Luxury SUV"]
        }
    
    def _get_kayak_location_id(self, branch_name: str) -> Optional[str]:
        """Get Kayak location ID for a Renty branch"""
        return self.location_mapping.get(branch_name)
    
    def _map_to_renty_category(self, vehicle_name: str, kayak_category: str) -> str:
        """
        Map Kayak category to Renty category using:
        1. Car model database (most accurate)
        2. Kayak category name
        """
        # Try car model mapping first (most accurate)
        renty_cat = get_correct_category(vehicle_name, kayak_category)
        if renty_cat != "Unknown":
            return renty_cat
        
        # Fall back to Kayak category mapping
        for renty_category, kayak_categories in self.category_mapping.items():
            if kayak_category in kayak_categories:
                return renty_category
        
        # Default fallback
        if 'suv' in kayak_category.lower():
            return "SUV Standard"
        elif any(x in kayak_category.lower() for x in ['luxury', 'premium']):
            return "Luxury Sedan"
        else:
            return "Standard"
    
    def _map_to_renty_category_price_aware(self, vehicle_name: str, kayak_category: str, price_per_day: float) -> str:
        """
        Map Kayak category to Renty category using car model database first.
        The car_model_category_mapping.py has the most accurate mappings.
        """
        # Use the car model database - it's the most accurate
        renty_cat = get_correct_category(vehicle_name, kayak_category)
        
        if renty_cat != "Unknown":
            return renty_cat
        
        # If not in database, use category mapping
        for renty_category, kayak_categories in self.category_mapping.items():
            if kayak_category in kayak_categories:
                return renty_category
        
        # Smart fallback based on keywords
        vehicle_upper = vehicle_name.upper()
        
        # Check for SUVs
        if any(x in vehicle_upper for x in ['SUV', 'X-TRAIL', 'RAV4', 'TUCSON', 'SPORTAGE', 'CRETA', 'KONA', 'QASHQAI']):
            # Small/Compact SUVs
            if any(x in kayak_category.lower() for x in ['compact', 'small']):
                return "SUV Compact"
            # Large SUVs
            elif any(x in vehicle_upper for x in ['LAND CRUISER', 'HIGHLANDER', 'PATROL', 'TAHOE', 'YUKON', 'SUBURBAN']):
                return "SUV Large"
            # Standard SUVs
            else:
                return "SUV Standard"
        
        # Check for luxury brands (sedans)
        if any(x in vehicle_upper for x in ['BMW', 'MERCEDES', 'AUDI', 'LEXUS']) and 'SUV' not in vehicle_upper:
            return "Luxury Sedan"
        
        # Check for pickup trucks
        if 'HILUX' in vehicle_upper or 'PICKUP' in vehicle_upper or 'pickup' in kayak_category.lower():
            return "Standard"
        
        # Default by Kayak category
        if kayak_category in ['Mini', 'Economy']:
            return "Economy"
        elif kayak_category == 'Compact':
            return "Compact"
        else:
            return "Standard"
    
    def search_cars(self, branch_name: str, pickup_date: date, dropoff_date: date) -> Dict[str, List[Dict]]:
        """
        Search for car rentals from Kayak for a specific branch and date range
        
        Returns:
            Dict mapping Renty categories to list of competitor prices
        """
        location_id = self._get_kayak_location_id(branch_name)
        if not location_id:
            logger.warning(f"No Kayak location mapping for branch: {branch_name}")
            return {}
        
        url = f"https://{self.host}/cars/search"
        
        params = {
            "pickupLocation": location_id,
            "dropoffLocation": location_id,
            "pickupDate": pickup_date.strftime("%Y-%m-%d"),
            "pickupHour": "10:00",
            "dropoffDate": dropoff_date.strftime("%Y-%m-%d"),
            "dropoffHour": "10:00",
            "currency": "SAR",
            "locale": "en-US",
            "sort": "rank_a",
            "priceMode": "total"
        }
        
        try:
            logger.info(f"Searching Kayak for {branch_name} ({location_id})")
            response = requests.get(url, headers=self.headers, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', {}).get('results', [])
                
                logger.info(f"Found {len(results)} cars from Kayak for {branch_name}")
                
                # Process results into categories
                category_prices = self._process_kayak_results(results, pickup_date, dropoff_date)
                return category_prices
            else:
                logger.error(f"Kayak API error: {response.status_code} - {response.text[:200]}")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching from Kayak: {str(e)}")
            return {}
    
    def _process_kayak_results(self, results: List[Dict], pickup_date: date, dropoff_date: date) -> Dict[str, List[Dict]]:
        """
        Process Kayak results into Renty categories
        
        Returns:
            Dict mapping Renty category to list of competitor prices
        """
        category_prices = {
            "Economy": [],
            "Compact": [],
            "Standard": [],
            "SUV Compact": [],
            "SUV Standard": [],
            "SUV Large": [],
            "Luxury Sedan": [],
            "Luxury SUV": []
        }
        
        rental_days = (dropoff_date - pickup_date).days
        if rental_days == 0:
            rental_days = 1
        
        for car in results:
            try:
                # Get supplier/agency
                agency_code = car.get('agencyCode', 'Unknown')
                
                # Get vehicle details from first provider
                providers = car.get('providers', [])
                if not providers:
                    continue
                
                provider = providers[0]
                vehicle_detail = provider.get('vehicleDetail', {})
                
                vehicle_name = vehicle_detail.get('brand', 'Unknown').strip()
                kayak_category = vehicle_detail.get('localizedCarClassName', 'Unknown').strip()
                
                # Get price
                day_price = provider.get('dayPrice', 0)
                currency = provider.get('currencyCode', 'SAR')
                
                # Convert USD to SAR if needed
                if currency == 'USD':
                    day_price = day_price * 3.75  # USD to SAR conversion
                
                # Skip if price is 0 or unreasonably high
                if day_price <= 0 or day_price > 5000:
                    continue
                
                # Map to Renty category (price-aware)
                renty_category = self._map_to_renty_category_price_aware(
                    vehicle_name, kayak_category, day_price
                )
                
                if renty_category in category_prices:
                    category_prices[renty_category].append({
                        'supplier': agency_code.title(),
                        'vehicle': vehicle_name,
                        'price_per_day': round(day_price, 2),
                        'category_original': kayak_category
                    })
            
            except Exception as e:
                logger.warning(f"Error processing Kayak car result: {str(e)}")
                continue
        
        # Deduplicate: Keep lowest price per supplier per category
        for category in category_prices.keys():
            prices = category_prices[category]
            if prices:
                # Keep lowest price per supplier
                supplier_best = {}
                for price in prices:
                    supplier = price['supplier']
                    if supplier not in supplier_best or price['price_per_day'] < supplier_best[supplier]['price_per_day']:
                        supplier_best[supplier] = price
                
                category_prices[category] = list(supplier_best.values())
        
        return category_prices
    
    def get_competitor_prices_for_dashboard(self, branch_name: str, date: date, **kwargs) -> Dict:
        """
        Get formatted competitor prices for dashboard display
        Compatible with existing dashboard interface
        """
        tomorrow = date + timedelta(days=1)
        day_after = date + timedelta(days=2)
        
        # Get prices for 2-day rental
        category_prices = self.search_cars(branch_name, tomorrow, day_after)
        
        # Return empty if no data
        if not category_prices:
            return {
                'avg_price': None,
                'min_price': None,
                'max_price': None,
                'competitors': [],
                'competitor_count': 0
            }
        
        # This will be called per category from dashboard
        category = kwargs.get('category', 'Economy')
        
        prices = category_prices.get(category, [])
        
        if not prices:
            return {
                'avg_price': None,
                'min_price': None,
                'max_price': None,
                'competitors': [],
                'competitor_count': 0
            }
        
        # Format for dashboard
        competitors = [
            {
                "Competitor_Name": p['supplier'],
                "Competitor_Price": p['price_per_day'],
                "Date": date.strftime('%Y-%m-%d %H:%M'),
                "Vehicle": p['vehicle']
            }
            for p in prices
        ]
        
        prices_list = [p['price_per_day'] for p in prices]
        
        return {
            'avg_price': round(sum(prices_list) / len(prices_list), 2),
            'min_price': min(prices_list),
            'max_price': max(prices_list),
            'competitors': competitors,
            'competitor_count': len(competitors)
        }


# Global instance
_kayak_client = None

def get_kayak_client() -> KayakAPI:
    """Get or create Kayak API client singleton"""
    global _kayak_client
    if _kayak_client is None:
        _kayak_client = KayakAPI()
    return _kayak_client


# For backward compatibility with dashboard
def get_competitor_prices_for_dashboard(category: str, branch_name: str, date: date, **kwargs) -> Dict:
    """Wrapper for dashboard compatibility"""
    client = get_kayak_client()
    return client.get_competitor_prices_for_dashboard(
        branch_name=branch_name,
        date=date,
        category=category,
        **kwargs
    )

