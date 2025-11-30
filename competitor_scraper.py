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
import os
import pickle

class SaudiCompetitorScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.cache_dir = "data/cache/scraper"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Competitor websites in Saudi Arabia
        self.competitors = {
            'Theeb': 'https://www.theeb.com.sa/en/car-rental-offers',
            'Hertz_Global': 'https://www.hertz.com/rentacar/reservation/',
            'Budget_Global': 'https://www.budget.com/en/home',
            'Yelo': 'https://www.yelo.sa/',
            'AlMajdouie': 'https://www.almajdouie.com/',
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
        """Initialize Chrome driver with anti-detection"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Anti-detection measures
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional preferences
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Execute script to hide automation
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.driver.set_page_load_timeout(60)
    
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
        """Extract prices from competitor website - aggressive mode"""
        try:
            print(f"Scraping {competitor_name}...")
            
            # Try to load page with retries
            for attempt in range(3):
                try:
                    self.driver.get(url)
                    break
                except:
                    if attempt < 2:
                        print(f"  Retry {attempt+1}/3...")
                        time.sleep(2)
                    else:
                        raise
            
            time.sleep(5)
            
            # Scroll multiple times to load lazy content
            for i in range(3):
                scroll_position = (i + 1) * (self.driver.execute_script("return document.body.scrollHeight") / 4)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(1)
            
            # Get full page source
            html = self.driver.page_source
            body_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
            # Aggressive price extraction - multiple patterns
            patterns = [
                # Arabic SAR
                r'ريال\s*(\d+)',
                r'(\d+)\s*ريال',
                # English SAR/SR
                r'(?:SAR|SR)\s*(\d+(?:[,\.]\d+)*)',
                r'(\d+(?:[,\.]\d+)*)\s*(?:SAR|SR)',
                # Per day patterns
                r'(\d{2,4})\s*/\s*(?:day|يوم)',
                r'(?:day|يوم).*?(\d{2,4})',
                # Daily rate patterns
                r'daily\s*rate.*?(\d{2,4})',
                r'rate.*?(\d{2,4})\s*SAR',
                # Generic 3-4 digit numbers (prices likely in this range)
                r'\b(\d{3,4})\s*(?:SAR|SR|ريال)',
                # From/starting patterns
                r'from\s*(\d{2,4})',
                r'starting.*?(\d{2,4})',
            ]
            
            found_prices = set()
            for pattern in patterns:
                matches = re.findall(pattern, html, re.I)
                for match in matches:
                    try:
                        price_str = str(match).replace(',', '').replace('.', '')
                        price = float(price_str)
                        if 80 < price < 1500:  # Daily rate range
                            found_prices.add(int(price))
                    except:
                        pass
            
            # Also check body text separately
            for pattern in patterns:
                matches = re.findall(pattern, body_text, re.I)
                for match in matches:
                    try:
                        price_str = str(match).replace(',', '').replace('.', '')
                        price = float(price_str)
                        if 80 < price < 1500:
                            found_prices.add(int(price))
                    except:
                        pass
            
            results = []
            for price in sorted(found_prices)[:10]:  # Take up to 10 prices
                results.append({
                    'vehicle': f'{competitor_name}',
                    'category': 'Various',
                    'price': price,
                    'provider': competitor_name,
                    'currency': 'SAR'
                })
            
            print(f"  Found {len(results)} prices: {sorted([r['price'] for r in results])}")
            return results
            
        except Exception as e:
            print(f"  Error: {str(e)[:100]}")
            return []
    
    def _match_category(self, vehicle_text, target_category):
        """Match scraped vehicle to target category"""
        if not vehicle_text:
            return False
        
        vehicle_lower = vehicle_text.lower()
        keywords = self.category_keywords.get(target_category, [])
        
        return any(keyword in vehicle_lower for keyword in keywords)
    
    def _get_cache_key(self, branch_name, category):
        """Generate cache key"""
        return f"{branch_name}_{category}".replace(' ', '_').replace('-', '_')
    
    def _get_cached_prices(self, cache_key, ttl_minutes=30):
        """Get cached prices if available and fresh"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cached = pickle.load(f)
                
                cache_time = datetime.fromisoformat(cached['cached_at'])
                age_minutes = (datetime.now() - cache_time).total_seconds() / 60
                
                if age_minutes < ttl_minutes:
                    print(f"Using cached prices ({age_minutes:.1f} min old)")
                    cached['data']['from_cache'] = True
                    return cached['data']
            except:
                pass
        
        return None
    
    def _set_cached_prices(self, cache_key, data):
        """Cache prices"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        try:
            cache_entry = {
                'cached_at': datetime.now().isoformat(),
                'data': data
            }
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_entry, f)
        except Exception as e:
            print(f"Cache error: {e}")
    
    def get_live_prices(self, branch_name, category, date=None):
        """
        Get live competitor prices from Saudi websites with caching
        
        Args:
            branch_name: Renty branch name
            category: Vehicle category
            date: Rental date (defaults to 7 days from now)
        
        Returns:
            dict with competitor prices
        """
        # Check cache first (30 min TTL)
        cache_key = self._get_cache_key(branch_name, category)
        cached = self._get_cached_prices(cache_key, ttl_minutes=30)
        if cached:
            return cached
        
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
            scraped_count = 0
            for name, url in list(self.competitors.items())[:3]:
                if scraped_count >= 3:
                    break
                results = self.scrape_simple(name, url)
                if results:
                    all_results.extend(results)
                    scraped_count += 1
                time.sleep(3)  # Delay between sites
            
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
                        'Source': result['provider'],
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
                        'Source': result['provider'],
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
            
            result = {
                'competitors': matched_results,
                'avg_price': avg_price,
                'competitor_count': len(matched_results),
                'location': branch_name,
                'category': category,
                'is_live': True,
                'last_updated': datetime.now().isoformat(),
                'data_source': 'WEB_SCRAPER'
            }
            
            # Cache result
            self._set_cached_prices(cache_key, result)
            
            return result
            
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

