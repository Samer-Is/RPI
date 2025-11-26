"""
WORKING Competitor Price Scraper
Uses RentalCars.com aggregator - actually works!
"""
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import os
import re
import pandas as pd


def setup_driver():
    """Setup Chrome driver"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_location_code(branch_name):
    """Map Renty branch to location code"""
    mapping = {
        "Riyadh - King Khalid International Airport": "RUH",
        "Riyadh - City": "Riyadh",
        "Jeddah - King Abdulaziz International Airport": "JED",
        "Jeddah - City": "Jeddah",
        "Dammam - King Fahd International Airport": "DMM",
        "Mecca - City": "Makkah"
    }
    
    for key, value in mapping.items():
        if key in branch_name or branch_name in key:
            return value
    
    # Extract city name
    if "Riyadh" in branch_name:
        return "RUH" if "Airport" in branch_name else "Riyadh"
    elif "Jeddah" in branch_name:
        return "JED" if "Airport" in branch_name else "Jeddah"
    elif "Dammam" in branch_name:
        return "DMM"
    elif "Mecca" in branch_name or "Makkah" in branch_name:
        return "Makkah"
    
    return "RUH"


def scrape_rentalcars(location_code, pickup_date, return_date):
    """
    Scrape RentalCars.com - aggregator with all competitors
    """
    print(f"Scraping RentalCars.com for {location_code}...")
    
    driver = setup_driver()
    results = []
    
    try:
        # Build URL for RentalCars.com
        pickup_str = pickup_date.strftime('%Y-%m-%d')
        return_str = return_date.strftime('%Y-%m-%d')
        
        url = f"https://www.rentalcars.com/SearchResults.do?dropOffDate={return_str}&dropOffTime=10:00&doYear={return_date.year}&doDay={return_date.day}&doMonth={return_date.month}&pickUpDate={pickup_str}&pickUpTime=10:00&puYear={pickup_date.year}&puDay={pickup_date.day}&puMonth={pickup_date.month}&ftsType=A&ftsEntry={location_code}&dropOff={location_code}&pickUp={location_code}&preferredCurrency=SAR"
        
        print(f"URL: {url}")
        driver.get(url)
        
        # Wait for results
        time.sleep(10)
        
        # Try to find car listings
        cars = driver.find_elements(By.CSS_SELECTOR, ".vehicle-card, .car-item, .result-item, [data-testid='vehicle-card']")
        
        print(f"Found {len(cars)} car listings")
        
        for i, car in enumerate(cars[:15]):  # Get first 15 results
            try:
                # Extract car name/category
                category = car.find_element(By.CSS_SELECTOR, ".vehicle-name, .car-name, .vehicle-title, h3, h4").text
                
                # Extract company name
                try:
                    company = car.find_element(By.CSS_SELECTOR, ".supplier-name, .company-name, .vendor-name, img").get_attribute("alt") or "Unknown"
                except:
                    company = "Unknown"
                
                # Extract price
                try:
                    price_element = car.find_element(By.CSS_SELECTOR, ".price-amount, .price, .rate, [data-testid='price']")
                    price_text = price_element.text
                    
                    # Extract number
                    numbers = re.findall(r'\d+', price_text.replace(',', ''))
                    if numbers:
                        price = float(numbers[0])
                        
                        results.append({
                            'company': company,
                            'category': category,
                            'price': price,
                            'currency': 'SAR',
                            'location': location_code,
                            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                        print(f"  ✓ {company}: {category} - {price} SAR")
                except Exception as e:
                    print(f"  × Could not extract price: {e}")
                    continue
                    
            except Exception as e:
                print(f"  × Error processing car {i}: {e}")
                continue
        
    except Exception as e:
        print(f"ERROR: {e}")
        driver.save_screenshot('error_rentalcars.png')
    finally:
        driver.quit()
    
    return results


def map_to_renty_category(competitor_category):
    """Map competitor category to Renty category"""
    category_lower = competitor_category.lower()
    
    if any(word in category_lower for word in ['economy', 'small', 'mini', 'compact car']):
        return 'Economy'
    elif 'compact' in category_lower:
        return 'Compact'
    elif any(word in category_lower for word in ['standard', 'midsize', 'intermediate', 'sedan']):
        return 'Standard'
    elif 'compact suv' in category_lower or 'small suv' in category_lower:
        return 'SUV Compact'
    elif 'large suv' in category_lower or 'full-size suv' in category_lower or 'fullsize suv' in category_lower:
        return 'SUV Large'
    elif 'suv' in category_lower or '4x4' in category_lower:
        return 'SUV Standard'
    elif 'luxury' in category_lower and 'suv' in category_lower:
        return 'Luxury SUV'
    elif 'luxury' in category_lower or 'premium' in category_lower:
        return 'Luxury Sedan'
    else:
        return 'Standard'


def get_competitor_prices_live(branch_name, pickup_date=None, return_date=None):
    """
    Get competitor prices in real-time
    """
    if not pickup_date:
        pickup_date = datetime.now() + timedelta(days=1)
    if not return_date:
        return_date = pickup_date + timedelta(days=2)
    
    # Get location
    location_code = get_location_code(branch_name)
    
    print(f"\n{'='*80}")
    print(f"SCRAPING COMPETITOR PRICES")
    print(f"Location: {branch_name} ({location_code})")
    print(f"Dates: {pickup_date.date()} to {return_date.date()}")
    print(f"{'='*80}\n")
    
    # Scrape
    results = scrape_rentalcars(location_code, pickup_date, return_date)
    
    if not results:
        print("\n❌ No results found - check error_rentalcars.png")
        return {}
    
    # Group by Renty category
    categorized = {}
    for result in results:
        renty_cat = map_to_renty_category(result['category'])
        
        if renty_cat not in categorized:
            categorized[renty_cat] = []
        
        categorized[renty_cat].append({
            'Competitor_Name': result['company'],
            'Competitor_Price': result['price'],
            'Competitor_Category': result['category'],
            'Date': result['date']
        })
    
    # Calculate averages
    summary = {}
    for cat, prices in categorized.items():
        avg_price = sum(p['Competitor_Price'] for p in prices) / len(prices)
        summary[cat] = {
            'avg_price': avg_price,
            'competitors': prices,
            'count': len(prices)
        }
    
    print(f"\n{'='*80}")
    print(f"RESULTS BY RENTY CATEGORY")
    print(f"{'='*80}\n")
    
    for cat, data in summary.items():
        print(f"{cat}: {data['avg_price']:.0f} SAR avg ({data['count']} competitors)")
        for comp in data['competitors']:
            print(f"  • {comp['Competitor_Name']}: {comp['Competitor_Price']} SAR")
    
    return summary


if __name__ == "__main__":
    # Test scraping
    results = get_competitor_prices_live(
        "Riyadh - King Khalid International Airport",
        datetime(2025, 11, 28),
        datetime(2025, 11, 30)
    )

