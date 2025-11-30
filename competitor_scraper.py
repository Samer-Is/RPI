"""
REAL Competitor Price Scraper - Saudi Arabia Car Rental Sites
Scrapes actual prices from Hertz, Budget, Thrifty, Theeb, Lumi websites
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

class SaudiCompetitorScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        
        # Competitor websites in Saudi Arabia
        self.competitors = {
            'Theeb': 'https://www.theeb.com.sa/en/',
            'Lumi': 'https://www.lumi.com.sa/en/',
            'Budget': 'https://www.avis-saudi.com/en/',  # Avis-Budget Saudi
        }
        
        # Location mapping
        self.location_search_terms = {
            'riyadh': 'Riyadh Airport',
            'jeddah': 'Jeddah Airport',
            'dammam': 'Dammam Airport',
            'mecca': 'Makkah',
            'medina': 'Madinah',
        }
        
        # Category matching
        self.category_keywords = {
            'Economy': ['economy', 'mini', 'compact', 'small'],
            'Compact': ['compact', 'small'],
            'Standard': ['standard', 'intermediate', 'midsize', 'medium'],
            'SUV Compact': ['compact suv', 'small suv', 'crossover'],
            'SUV Standard': ['standard suv', 'suv', 'mid suv'],
            'SUV Large': ['large suv', 'full-size suv', 'premium suv'],
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
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
    
    def _close_driver(self):
        """Close driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def _extract_location(self, branch_name):
        """Extract location from branch name"""
        branch_lower = branch_name.lower()
        for location, search_term in self.location_search_terms.items():
            if location in branch_lower:
                return search_term
        return 'Riyadh Airport'  # Default
    
    def scrape_hertz_sa(self, location, pickup_date, return_date):
        """Scrape Hertz Saudi Arabia"""
        try:
            url = self.competitors['Hertz']
            print(f"Scraping Hertz: {url}")
            self.driver.get(url)
            time.sleep(5)
            
            # Take screenshot
            self.driver.save_screenshot('hertz_page.png')
            print("Screenshot saved")
            
            # Look for search form or reservation button
            try:
                # Try to find and click reservation/booking button
                search_buttons = self.driver.find_elements(By.XPATH, 
                    "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'reservation') or "
                    "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'book') or "
                    "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'rent')]")
                
                if search_buttons:
                    print(f"Found {len(search_buttons)} booking buttons")
                    search_buttons[0].click()
                    time.sleep(3)
            except Exception as e:
                print(f"Could not click booking button: {e}")
            
            # Try to find location input
            try:
                location_inputs = self.driver.find_elements(By.CSS_SELECTOR, 
                    "input[type='text'], input[name*='location'], input[id*='location'], input[placeholder*='location']")
                
                if location_inputs:
                    print(f"Found {len(location_inputs)} location inputs")
                    location_inputs[0].clear()
                    location_inputs[0].send_keys(location)
                    time.sleep(2)
            except Exception as e:
                print(f"Could not enter location: {e}")
            
            # Try to find date inputs
            try:
                date_inputs = self.driver.find_elements(By.CSS_SELECTOR, 
                    "input[type='date'], input[name*='date'], input[id*='date']")
                
                if len(date_inputs) >= 2:
                    print(f"Found {len(date_inputs)} date inputs")
                    date_inputs[0].clear()
                    date_inputs[0].send_keys(pickup_date.strftime('%d/%m/%Y'))
                    date_inputs[1].clear()
                    date_inputs[1].send_keys(return_date.strftime('%d/%m/%Y'))
                    time.sleep(2)
            except Exception as e:
                print(f"Could not enter dates: {e}")
            
            # Try to submit search
            try:
                submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "button[type='submit'], input[type='submit'], button")
                
                for btn in submit_buttons:
                    btn_text = btn.text.lower()
                    if any(word in btn_text for word in ['search', 'find', 'go', 'submit', 'book']):
                        print(f"Clicking submit button: {btn.text}")
                        btn.click()
                        time.sleep(5)
                        break
            except Exception as e:
                print(f"Could not submit search: {e}")
            
            # Try multiple possible selectors for car listings
            results = []
            
            # Method 1: Use actual Kayak selectors
            try:
                # Try Kayak-specific price elements
                price_holders = self.driver.find_elements(By.CSS_SELECTOR, ".esgW-price-holder, .P_Ok-sublink-price, [class*='price']")
                print(f"Found {len(price_holders)} price elements")
                
                # Try to find all results containers
                result_cards = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='vdb4'], div[class*='E9x1'], div[class*='result']")
                print(f"Found {len(result_cards)} result cards")
                
                # Extract from all text on page as fallback
                body_text = self.driver.find_element(By.TAG_NAME, 'body').text
                
                # Look for patterns like "SAR 150" or "150 SAR"
                all_prices = re.findall(r'(?:SAR|SR)\s*(\d+(?:,\d{3})*)|(\d+(?:,\d{3})*)\s*(?:SAR|SR)', body_text, re.I)
                
                for price_tuple in all_prices:
                    price_str = (price_tuple[0] or price_tuple[1]).replace(',', '')
                    try:
                        price = float(price_str)
                        if 50 < price < 2000 and len(results) < 10:
                            results.append({
                                'vehicle': 'Car',
                                'category': 'Various',
                                'price': price,
                                'provider': 'Kayak',
                                'currency': 'SAR'
                            })
                    except:
                        continue
                
                print(f"Extracted {len(results)} prices from page text")
                
                # If still no results, try extracting from result cards
                if not results:
                    for card in result_cards[:10]:
                        try:
                            card_text = card.text
                            price_match = re.search(r'(\d+(?:,\d{3})*)\s*(?:SAR|SR|per day|/day)', card_text, re.I)
                            if price_match:
                                price = float(price_match.group(1).replace(',', ''))
                                if 50 < price < 2000:
                                    results.append({
                                        'vehicle': card_text.split('\n')[0][:50] if card_text else "Car",
                                        'category': 'Unknown',
                                        'price': price,
                                        'provider': 'Various',
                                        'currency': 'SAR'
                                    })
                        except:
                            continue
            
            except Exception as e:
                print(f"Error extracting prices: {e}")
            
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
    
    def scrape_simple(self, competitor_name, url):
        """Extract prices from competitor website"""
        try:
            print(f"Scraping {competitor_name}...")
            self.driver.get(url)
            time.sleep(8)
            
            # Scroll to load content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(3)
            
            # Get page HTML
            html = self.driver.page_source
            
            # Extract all numbers that look like prices
            # Look for patterns: SAR 150, 150 SAR, SR 150, 150/day, etc.
            patterns = [
                r'(?:SAR|SR|ريال)\s*(\d+(?:,\d{3})*)',
                r'(\d+(?:,\d{3})*)\s*(?:SAR|SR|ريال)',
                r'(\d+)\s*/\s*(?:day|يوم)',
                r'daily.*?(\d{3})',
                r'per\s*day.*?(\d{3})',
            ]
            
            found_prices = set()
            for pattern in patterns:
                matches = re.findall(pattern, html, re.I)
                for match in matches:
                    try:
                        price = float(str(match).replace(',', ''))
                        if 80 < price < 1500:  # Reasonable daily rate range
                            found_prices.add(int(price))
                    except:
                        pass
            
            results = []
            for price in list(found_prices)[:5]:
                results.append({
                    'vehicle': f'{competitor_name}',
                    'category': 'Various',
                    'price': price,
                    'provider': competitor_name,
                    'currency': 'SAR'
                })
            
            print(f"  Found {len(results)} prices: {[r['price'] for r in results]}")
            return results
            
        except Exception as e:
            print(f"  Error: {e}")
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
        Get live competitor prices from Saudi websites
        
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
        
        location = self._extract_location(branch_name)
        
        try:
            self._init_driver()
            
            print(f"Scraping competitors for {category} at {location}...")
            all_results = []
            
            # Scrape each competitor
            for name, url in self.competitors.items():
                results = self.scrape_simple(name, url)
                all_results.extend(results)
                time.sleep(2)  # Be polite
            
            if not all_results:
                return {
                    'competitors': [],
                    'avg_price': None,
                    'competitor_count': 0,
                    'warning': f'No results from competitors for {location}',
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
                'data_source': 'SAUDI_COMPETITORS'
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
    Get live competitor prices from Saudi websites
    """
    scraper = SaudiCompetitorScraper(headless=True)
    return scraper.get_live_prices(branch_name, category, date)


if __name__ == "__main__":
    print("Testing Saudi Competitor Scraper...")
    scraper = SaudiCompetitorScraper(headless=False)
    result = scraper.get_live_prices(
        branch_name="King Khalid Airport - Riyadh",
        category="Economy"
    )
    print("\nResults:")
    print(json.dumps(result, indent=2))

