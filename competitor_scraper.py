"""
REAL Competitor Price Scraper
Scrapes actual prices from competitor websites using Selenium
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta
import time
import json
import os

class CompetitorScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        
        # Location mapping: Renty branch name -> Competitor search terms
        self.location_mapping = {
            'riyadh': ['Riyadh', 'King Khalid Airport', 'RUH'],
            'jeddah': ['Jeddah', 'King Abdulaziz Airport', 'JED'],
            'dammam': ['Dammam', 'King Fahd Airport', 'DMM'],
            'mecca': ['Makkah', 'Mecca'],
            'medina': ['Madinah', 'Medina'],
        }
        
        # Category mapping: Renty -> Competitor terms
        self.category_mapping = {
            'Economy': ['Economy', 'Compact Car', 'Mini'],
            'Compact': ['Compact', 'Economy', 'Small'],
            'Standard': ['Standard', 'Intermediate', 'Midsize'],
            'SUV Compact': ['Compact SUV', 'Small SUV', 'Crossover'],
            'SUV Standard': ['Standard SUV', 'SUV', 'Mid SUV'],
            'SUV Large': ['Large SUV', 'Full-size SUV', 'Premium SUV'],
            'Luxury Sedan': ['Luxury', 'Premium', 'Executive'],
            'Luxury SUV': ['Luxury SUV', 'Premium SUV', 'Executive SUV']
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
    
    def _extract_location_key(self, branch_name):
        """Extract location keyword from branch name"""
        branch_lower = branch_name.lower()
        for key in self.location_mapping.keys():
            if key in branch_lower:
                return key
        return 'riyadh'  # Default
    
    def scrape_hertz(self, location, category, pickup_date, return_date):
        """Scrape Hertz Saudi Arabia"""
        try:
            url = "https://www.hertz.com.sa/rentacar/reservation/"
            self.driver.get(url)
            time.sleep(3)
            
            # Fill location
            location_terms = self.location_mapping.get(location, ['Riyadh'])
            location_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "pickup-location"))
            )
            location_input.clear()
            location_input.send_keys(location_terms[0])
            time.sleep(2)
            
            # Fill dates
            pickup_input = self.driver.find_element(By.ID, "pickup-date")
            pickup_input.clear()
            pickup_input.send_keys(pickup_date.strftime('%d/%m/%Y'))
            
            return_input = self.driver.find_element(By.ID, "return-date")
            return_input.clear()
            return_input.send_keys(return_date.strftime('%d/%m/%Y'))
            
            # Submit search
            search_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            search_btn.click()
            
            # Wait for results
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "vehicle-card"))
            )
            time.sleep(2)
            
            # Find matching category
            vehicles = self.driver.find_elements(By.CLASS_NAME, "vehicle-card")
            category_terms = self.category_mapping.get(category, [category])
            
            for vehicle in vehicles:
                vehicle_name = vehicle.find_element(By.CLASS_NAME, "vehicle-name").text
                vehicle_category = vehicle.find_element(By.CLASS_NAME, "vehicle-category").text
                
                # Check if matches category
                if any(term.lower() in vehicle_category.lower() or term.lower() in vehicle_name.lower() 
                       for term in category_terms):
                    price_elem = vehicle.find_element(By.CLASS_NAME, "price-per-day")
                    price_text = price_elem.text
                    
                    # Extract number from price text
                    import re
                    price_match = re.search(r'(\d+(?:\.\d+)?)', price_text.replace(',', ''))
                    if price_match:
                        price = float(price_match.group(1))
                        return {
                            'competitor': 'Hertz',
                            'price': price,
                            'category': vehicle_category,
                            'vehicle': vehicle_name,
                            'currency': 'SAR',
                            'scraped_at': datetime.now().isoformat()
                        }
            
            return None
            
        except Exception as e:
            print(f"Hertz scraping error: {e}")
            return None
    
    def scrape_budget(self, location, category, pickup_date, return_date):
        """Scrape Budget Saudi Arabia"""
        try:
            url = "https://www.budget.com.sa/"
            self.driver.get(url)
            time.sleep(3)
            
            # Similar logic to Hertz
            # Each site will have different selectors
            
            return None  # Placeholder
            
        except Exception as e:
            print(f"Budget scraping error: {e}")
            return None
    
    def get_live_prices(self, branch_name, category, date=None):
        """
        Get live competitor prices for given branch and category
        
        Args:
            branch_name: Renty branch name (e.g., "King Khalid Airport - Riyadh")
            category: Vehicle category (e.g., "Economy")
            date: Rental date (defaults to 7 days from now)
        
        Returns:
            dict with competitor prices
        """
        if date is None:
            date = datetime.now() + timedelta(days=7)
        
        pickup_date = date
        return_date = date + timedelta(days=1)
        
        location_key = self._extract_location_key(branch_name)
        
        prices = []
        
        try:
            self._init_driver()
            
            # Scrape Hertz
            print(f"Scraping Hertz for {category} at {location_key}...")
            hertz_price = self.scrape_hertz(location_key, category, pickup_date, return_date)
            if hertz_price:
                prices.append(hertz_price)
            
            # Scrape Budget
            print(f"Scraping Budget for {category} at {location_key}...")
            budget_price = self.scrape_budget(location_key, category, pickup_date, return_date)
            if budget_price:
                prices.append(budget_price)
            
            # Add more competitors here
            
        except Exception as e:
            print(f"Scraping error: {e}")
        finally:
            self._close_driver()
        
        if not prices:
            return {
                'competitors': [],
                'avg_price': None,
                'competitor_count': 0,
                'warning': 'Failed to scrape competitor prices',
                'location': branch_name,
                'category': category,
                'is_live': False
            }
        
        avg_price = sum(p['price'] for p in prices) / len(prices)
        
        return {
            'competitors': prices,
            'avg_price': avg_price,
            'competitor_count': len(prices),
            'location': branch_name,
            'category': category,
            'is_live': True,
            'last_updated': datetime.now().isoformat()
        }


# Dashboard integration function
def get_competitor_prices_for_dashboard(category, branch_name, date, **kwargs):
    """
    Get live competitor prices for dashboard
    """
    scraper = CompetitorScraper(headless=True)
    return scraper.get_live_prices(branch_name, category, date)


if __name__ == "__main__":
    scraper = CompetitorScraper(headless=False)
    result = scraper.get_live_prices(
        branch_name="King Khalid Airport - Riyadh",
        category="Economy"
    )
    print(json.dumps(result, indent=2))

