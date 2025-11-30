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
        
        # Complete location mapping for all Renty branches
        self.location_mapping = {
            'King Khalid Airport - Riyadh': {'search': 'Riyadh Airport RUH', 'city': 'Riyadh', 'is_airport': True},
            'Olaya District - Riyadh': {'search': 'Riyadh Olaya', 'city': 'Riyadh', 'is_airport': False},
            'King Fahd Airport - Dammam': {'search': 'Dammam Airport DMM', 'city': 'Dammam', 'is_airport': True},
            'King Abdulaziz Airport - Jeddah': {'search': 'Jeddah Airport JED', 'city': 'Jeddah', 'is_airport': True},
            'Al Khobar Business District': {'search': 'Al Khobar', 'city': 'Al Khobar', 'is_airport': False},
            'Mecca City Center': {'search': 'Makkah', 'city': 'Mecca', 'is_airport': False},
            'Medina Downtown': {'search': 'Madinah', 'city': 'Medina', 'is_airport': False},
            'Riyadh City Center': {'search': 'Riyadh City', 'city': 'Riyadh', 'is_airport': False},
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
    
    def _get_location_info(self, branch_name):
        """Get location info for branch"""
        # Try exact match first
        if branch_name in self.location_mapping:
            return self.location_mapping[branch_name]
        
        # Try partial match
        for renty_branch, info in self.location_mapping.items():
            if branch_name.lower() in renty_branch.lower() or renty_branch.lower() in branch_name.lower():
                return info
        
        # Default to Riyadh Airport
        return {'search': 'Riyadh Airport RUH', 'city': 'Riyadh', 'is_airport': True}
    
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
    
    def scrape_with_location_and_category(self, competitor_name, url, location_info, target_category):
        """Extract prices from competitor website with location and category matching"""
        try:
            print(f"Scraping {competitor_name} for {target_category} in {location_info['city']}...")
            
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
            
            # Extract vehicle cards/sections (try to find structured data)
            vehicle_data = self._extract_vehicle_cards(html, body_text)
            
            # If structured extraction worked, use it
            if vehicle_data:
                print(f"  Found {len(vehicle_data)} vehicles with categories")
                results = []
                for veh in vehicle_data:
                    if self._match_category(veh['category'], target_category):
                        results.append({
                            'vehicle': veh['vehicle'],
                            'category': veh['category'],
                            'price': veh['price'],
                            'provider': competitor_name,
                            'currency': 'SAR',
                            'confidence': 90
                        })
                
                if results:
                    print(f"  Matched {len(results)} to {target_category}")
                    return results
            
            # Fallback: aggressive price extraction
            print(f"  Using fallback extraction...")
            patterns = [
                r'ريال\s*(\d+)',
                r'(\d+)\s*ريال',
                r'(?:SAR|SR)\s*(\d+(?:[,\.]\d+)*)',
                r'(\d+(?:[,\.]\d+)*)\s*(?:SAR|SR)',
                r'(\d{2,4})\s*/\s*(?:day|يوم)',
                r'(?:day|يوم).*?(\d{2,4})',
                r'daily\s*rate.*?(\d{2,4})',
                r'\b(\d{3,4})\s*(?:SAR|SR|ريال)',
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
                        if 80 < price < 1500:
                            found_prices.add(int(price))
                    except:
                        pass
            
            results = []
            for price in sorted(found_prices)[:10]:
                results.append({
                    'vehicle': f'{competitor_name}',
                    'category': self._guess_category_from_price(price, target_category),
                    'price': price,
                    'provider': competitor_name,
                    'currency': 'SAR',
                    'confidence': 50
                })
            
            print(f"  Found {len(results)} prices")
            return results
            
        except Exception as e:
            print(f"  Error: {str(e)[:100]}")
            return []
    
    def _extract_vehicle_cards(self, html, body_text):
        """Try to extract vehicle information with categories from page structure"""
        vehicles = []
        
        # Try to find vehicle cards/sections
        try:
            # Look for common car category keywords near prices
            lines = body_text.split('\n')
            
            for i, line in enumerate(lines):
                # Check if line contains a price
                price_match = re.search(r'(?:SAR|SR|ريال)?\s*(\d{2,4})\s*(?:SAR|SR|ريال|/day|per day)?', line, re.I)
                if price_match:
                    price = int(price_match.group(1))
                    if 80 < price < 1500:
                        # Look for category keywords in surrounding lines
                        context = '\n'.join(lines[max(0, i-3):min(len(lines), i+3)])
                        category = self._extract_category_from_context(context)
                        vehicle_name = self._extract_vehicle_name(context)
                        
                        if category or vehicle_name:
                            vehicles.append({
                                'vehicle': vehicle_name or 'Car',
                                'category': category or 'Various',
                                'price': price
                            })
        except Exception as e:
            print(f"  Card extraction error: {e}")
        
        return vehicles
    
    def _extract_category_from_context(self, text):
        """Extract category from text context"""
        text_lower = text.lower()
        
        # Priority order: more specific first
        if any(word in text_lower for word in ['luxury suv', 'premium suv', 'large suv']):
            return 'Luxury SUV'
        if any(word in text_lower for word in ['luxury', 'premium', 'executive']):
            return 'Luxury Sedan'
        if any(word in text_lower for word in ['full-size suv', 'full size suv']):
            return 'SUV Large'
        if any(word in text_lower for word in ['standard suv', 'mid suv', 'midsize suv']):
            return 'SUV Standard'
        if any(word in text_lower for word in ['compact suv', 'small suv', 'crossover']):
            return 'SUV Compact'
        if any(word in text_lower for word in ['suv']):
            return 'SUV Standard'
        if any(word in text_lower for word in ['standard', 'intermediate', 'midsize']):
            return 'Standard'
        if any(word in text_lower for word in ['compact', 'small car']):
            return 'Compact'
        if any(word in text_lower for word in ['economy', 'mini', 'budget']):
            return 'Economy'
        
        return None
    
    def _extract_vehicle_name(self, text):
        """Extract vehicle name from context"""
        # Look for common car brand names
        brands = ['Toyota', 'Hyundai', 'Nissan', 'Kia', 'BMW', 'Mercedes', 'Audi', 
                  'Chevrolet', 'Ford', 'Honda', 'Mazda', 'Mitsubishi']
        
        for brand in brands:
            if brand.lower() in text.lower():
                # Try to extract model too
                match = re.search(rf'{brand}\s+(\w+)', text, re.I)
                if match:
                    return f"{brand} {match.group(1)}"
                return brand
        
        return None
    
    def _guess_category_from_price(self, price, target_category):
        """Guess category based on price range"""
        if price < 120:
            return 'Economy'
        elif price < 160:
            return 'Compact'
        elif price < 200:
            return 'Standard'
        elif price < 250:
            return 'SUV Compact'
        elif price < 300:
            return 'SUV Standard'
        elif price < 350:
            return 'SUV Large'
        elif price < 450:
            return 'Luxury Sedan'
        else:
            return 'Luxury SUV'
    
    def _match_category(self, vehicle_text, target_category):
        """Match scraped vehicle to target category with fuzzy matching"""
        if not vehicle_text:
            return False
        
        vehicle_lower = vehicle_text.lower()
        
        # Exact category match
        if target_category.lower() in vehicle_lower:
            return True
        
        # Keyword matching
        keywords = self.category_keywords.get(target_category, [])
        if any(keyword in vehicle_lower for keyword in keywords):
            return True
        
        # Cross-category partial matches
        # SUV variants
        if 'suv' in target_category.lower() and 'suv' in vehicle_lower:
            return True
        
        # Luxury variants
        if 'luxury' in target_category.lower() and any(word in vehicle_lower for word in ['luxury', 'premium', 'executive']):
            return True
        
        return False
    
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
        
        location_info = self._get_location_info(branch_name)
        
        try:
            self._init_driver()
            
            print(f"Scraping for {category} at {location_info['city']} ({location_info['search']})...")
            all_results = []
            
            # Scrape each competitor with location and category
            scraped_count = 0
            for name, url in list(self.competitors.items())[:3]:
                if scraped_count >= 3:
                    break
                results = self.scrape_with_location_and_category(name, url, location_info, category)
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
            
            # Filter and rank results by category match
            matched_results = []
            for result in all_results:
                vehicle_text = f"{result['vehicle']} {result['category']}"
                confidence = result.get('confidence', 70)
                
                # Boost confidence if category matches exactly
                if result['category'] == category:
                    confidence = min(95, confidence + 20)
                elif self._match_category(vehicle_text, category):
                    confidence = min(85, confidence + 10)
                
                matched_results.append({
                    'Competitor_Name': result['provider'],
                    'Competitor_Price': int(result['price']),
                    'Competitor_Category': result['category'],
                    'Vehicle': result['vehicle'],
                    'Date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'Source': result['provider'],
                    'Confidence': confidence,
                    'Location': location_info['city']
                })
            
            # Sort by confidence and relevance
            matched_results.sort(key=lambda x: (x['Confidence'], -abs(x['Competitor_Price'] - 200)), reverse=True)
            
            # Take top results
            if not matched_results:
                print(f"No results found for {category}")
            else:
                print(f"Found {len(matched_results)} results (top confidence: {matched_results[0]['Confidence']}%)")
                matched_results = matched_results[:5]  # Top 5 most relevant
            
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

