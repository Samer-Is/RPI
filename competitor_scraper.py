"""
REAL Competitor Price Scraper via Kayak
Scrapes actual rental car prices from Kayak.com using Selenium
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
import time
import json
import re

class KayakScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.base_url = "https://www.kayak.com/cars"
        
        # Airport codes for Saudi Arabia
        self.airport_codes = {
            'riyadh': 'RUH',
            'jeddah': 'JED',
            'dammam': 'DMM',
            'mecca': 'JED',  # Closest airport
            'medina': 'MED',
            'abha': 'AHB',
            'tabuk': 'TUU',
            'najran': 'EAM'
        }
        
        # Category matching keywords
        self.category_keywords = {
            'Economy': ['economy', 'mini', 'compact'],
            'Compact': ['compact', 'small'],
            'Standard': ['standard', 'intermediate', 'midsize', 'mid-size'],
            'SUV Compact': ['compact suv', 'small suv', 'crossover'],
            'SUV Standard': ['standard suv', 'suv', 'mid suv'],
            'SUV Large': ['large suv', 'full-size suv', 'fullsize suv', 'premium suv'],
            'Luxury Sedan': ['luxury', 'premium', 'executive'],
            'Luxury SUV': ['luxury suv', 'premium suv']
        }
    
    def _init_driver(self):
        """Initialize Chrome driver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
    
    def _close_driver(self):
        """Close driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def _extract_airport_code(self, branch_name):
        """Extract airport code from branch name"""
        branch_lower = branch_name.lower()
        for location, code in self.airport_codes.items():
            if location in branch_lower:
                return code
        return 'RUH'  # Default to Riyadh
    
    def scrape_kayak(self, airport_code, pickup_date, return_date):
        """
        Scrape Kayak for all car rental prices at given location
        
        Args:
            airport_code: IATA code (e.g., 'RUH' for Riyadh)
            pickup_date: datetime object
            return_date: datetime object
        
        Returns:
            List of dicts with car rental results
        """
        try:
            # Build Kayak URL
            pickup_str = pickup_date.strftime('%Y-%m-%d')
            return_str = return_date.strftime('%Y-%m-%d')
            pickup_time = '10:00'
            return_time = '10:00'
            
            url = f"{self.base_url}/{airport_code}-a/{pickup_str}-{pickup_time}/{return_str}-{return_time}?sort=rank_a"
            
            print(f"Navigating to Kayak: {url}")
            self.driver.get(url)
            
            # Wait for results to load
            print("Waiting for results...")
            time.sleep(8)  # Kayak needs time to load search results
            
            # Try multiple possible selectors for car listings
            results = []
            
            # Method 1: Try div with car listings
            try:
                car_cards = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='car'], div[data-resultid]")
                print(f"Found {len(car_cards)} car cards")
                
                for card in car_cards[:20]:  # Limit to first 20 results
                    try:
                        # Extract car details
                        car_name = ""
                        car_category = ""
                        price = None
                        provider = ""
                        
                        # Try to find car name/category
                        try:
                            name_elem = card.find_element(By.CSS_SELECTOR, "[class*='name'], [class*='title'], h3, h4")
                            car_name = name_elem.text.strip()
                        except:
                            pass
                        
                        # Try to find car category
                        try:
                            category_elem = card.find_element(By.CSS_SELECTOR, "[class*='category'], [class*='type']")
                            car_category = category_elem.text.strip()
                        except:
                            pass
                        
                        # Try to find price
                        try:
                            price_elems = card.find_elements(By.CSS_SELECTOR, "[class*='price'], [class*='rate']")
                            for price_elem in price_elems:
                                price_text = price_elem.text
                                # Look for SAR prices or dollar prices
                                price_match = re.search(r'(?:SAR|SR|﷼)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)', price_text)
                                if price_match:
                                    price_str = price_match.group(1).replace(',', '')
                                    price = float(price_str)
                                    break
                        except:
                            pass
                        
                        # Try to find provider
                        try:
                            provider_elem = card.find_element(By.CSS_SELECTOR, "[class*='provider'], [class*='supplier'], [class*='vendor']")
                            provider = provider_elem.text.strip()
                        except:
                            pass
                        
                        # Add result if we have minimum data
                        if (car_name or car_category) and price and price > 0:
                            results.append({
                                'vehicle': car_name,
                                'category': car_category,
                                'price': price,
                                'provider': provider if provider else 'Unknown',
                                'currency': 'SAR'
                            })
                    
                    except Exception as e:
                        continue
            
            except Exception as e:
                print(f"Error extracting car cards: {e}")
            
            # If no results, try to get any price on page
            if not results:
                print("Trying alternative extraction method...")
                all_text = self.driver.find_element(By.TAG_NAME, 'body').text
                # Look for prices in page text
                price_matches = re.findall(r'(?:SAR|SR)\s*(\d+(?:,\d{3})*)', all_text)
                if price_matches:
                    print(f"Found {len(price_matches)} prices in page text")
                    for price_str in price_matches[:5]:
                        price = float(price_str.replace(',', ''))
                        if 50 < price < 2000:  # Reasonable price range
                            results.append({
                                'vehicle': 'Car',
                                'category': 'Unknown',
                                'price': price,
                                'provider': 'Kayak',
                                'currency': 'SAR'
                            })
            
            return results
            
        except Exception as e:
            print(f"Kayak scraping error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _match_category(self, vehicle_text, target_category):
        """Match scraped vehicle to target category"""
        if not vehicle_text:
            return False
        
        vehicle_lower = vehicle_text.lower()
        keywords = self.category_keywords.get(target_category, [])
        
        return any(keyword in vehicle_lower for keyword in keywords)
    
    def get_live_prices(self, branch_name, category, date=None):
        """
        Get live competitor prices from Kayak
        
        Args:
            branch_name: Renty branch name
            category: Vehicle category
            date: Rental date (defaults to 7 days from now)
        
        Returns:
            dict with competitor prices
        """
        if date is None:
            date = datetime.now() + timedelta(days=7)
        
        pickup_date = date
        return_date = date + timedelta(days=1)
        
        airport_code = self._extract_airport_code(branch_name)
        
        try:
            self._init_driver()
            
            print(f"Scraping Kayak for {category} at {airport_code}...")
            all_results = self.scrape_kayak(airport_code, pickup_date, return_date)
            
            if not all_results:
                return {
                    'competitors': [],
                    'avg_price': None,
                    'competitor_count': 0,
                    'warning': f'No results from Kayak for {airport_code}',
                    'location': branch_name,
                    'category': category,
                    'is_live': False
                }
            
            # Filter results that match requested category
            matched_results = []
            for result in all_results:
                vehicle_text = f"{result['vehicle']} {result['category']}"
                if self._match_category(vehicle_text, category):
                    matched_results.append({
                        'Competitor_Name': result['provider'],
                        'Competitor_Price': int(result['price']),
                        'Competitor_Category': result['category'],
                        'Vehicle': result['vehicle'],
                        'Date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'Source': 'Kayak',
                        'Confidence': 95
                    })
            
            # If no exact matches, use closest prices
            if not matched_results and all_results:
                print(f"No exact match for {category}, using available results")
                for result in all_results[:3]:  # Take first 3
                    matched_results.append({
                        'Competitor_Name': result['provider'],
                        'Competitor_Price': int(result['price']),
                        'Competitor_Category': result['category'],
                        'Vehicle': result['vehicle'],
                        'Date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'Source': 'Kayak',
                        'Confidence': 70
                    })
            
            if not matched_results:
                return {
                    'competitors': [],
                    'avg_price': None,
                    'competitor_count': 0,
                    'warning': f'No {category} vehicles found',
                    'location': branch_name,
                    'category': category,
                    'is_live': False
                }
            
            avg_price = sum(r['Competitor_Price'] for r in matched_results) / len(matched_results)
            
            return {
                'competitors': matched_results,
                'avg_price': avg_price,
                'competitor_count': len(matched_results),
                'location': branch_name,
                'category': category,
                'is_live': True,
                'last_updated': datetime.now().isoformat(),
                'data_source': 'KAYAK_SCRAPER'
            }
            
        except Exception as e:
            print(f"Scraping error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'competitors': [],
                'avg_price': None,
                'competitor_count': 0,
                'warning': f'Scraping failed: {str(e)}',
                'location': branch_name,
                'category': category,
                'is_live': False
            }
        finally:
            self._close_driver()


# Dashboard integration function
def get_competitor_prices_for_dashboard(category, branch_name, date, **kwargs):
    """
    Get live competitor prices from Kayak for dashboard
    """
    scraper = KayakScraper(headless=True)
    return scraper.get_live_prices(branch_name, category, date)


if __name__ == "__main__":
    print("Testing Kayak Scraper...")
    scraper = KayakScraper(headless=False)
    result = scraper.get_live_prices(
        branch_name="King Khalid Airport - Riyadh",
        category="Economy"
    )
    print("\nResults:")
    print(json.dumps(result, indent=2))

