"""
Inspect competitor websites to find correct selectors for scraping
Run this to see website structure and update competitor_scraper.py with correct selectors
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def inspect_hertz():
    """Inspect Hertz website structure"""
    print("="*80)
    print("INSPECTING HERTZ.COM.SA")
    print("="*80)
    
    options = Options()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get("https://www.hertz.com.sa/")
        print(f"Loaded: {driver.title}")
        print("\nWaiting 10 seconds for you to manually:")
        print("1. Search for: Riyadh Airport")
        print("2. Date: 7 days from now")
        print("3. Duration: 1 day")
        print("4. Click Search")
        print("\nScript will capture page structure after search...")
        
        time.sleep(10)
        
        # Try to find common elements
        print("\n" + "-"*80)
        print("Searching for price elements...")
        print("-"*80)
        
        possible_selectors = [
            ("class", "price"),
            ("class", "vehicle-price"),
            ("class", "rate"),
            ("class", "daily-rate"),
            ("class", "car-price"),
            ("xpath", "//*[contains(@class, 'price')]"),
            ("xpath", "//*[contains(text(), 'SAR')]"),
        ]
        
        for selector_type, selector_value in possible_selectors:
            try:
                if selector_type == "class":
                    elements = driver.find_elements(By.CLASS_NAME, selector_value)
                elif selector_type == "xpath":
                    elements = driver.find_elements(By.XPATH, selector_value)
                
                if elements:
                    print(f"\nFound {len(elements)} elements with {selector_type}='{selector_value}':")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        try:
                            text = elem.text
                            if text:
                                print(f"  [{i}] {text[:100]}")
                        except:
                            pass
            except:
                pass
        
        print("\n" + "-"*80)
        print("Page Source Sample (first 2000 chars):")
        print("-"*80)
        print(driver.page_source[:2000])
        
        input("\nPress Enter to close browser...")
        
    finally:
        driver.quit()

def inspect_budget():
    """Inspect Budget website structure"""
    print("="*80)
    print("INSPECTING BUDGET.COM.SA")
    print("="*80)
    
    options = Options()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get("https://www.budget.com.sa/")
        print(f"Loaded: {driver.title}")
        print("\nDo manual search, then press Enter...")
        input()
        
        # Similar inspection logic
        print("Page title:", driver.title)
        print("URL:", driver.current_url)
        
        input("\nPress Enter to close...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    print("COMPETITOR WEBSITE INSPECTOR")
    print("This tool helps find correct selectors for scraping")
    print()
    print("Choose:")
    print("1. Inspect Hertz")
    print("2. Inspect Budget")
    print("3. Inspect Thrifty")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        inspect_hertz()
    elif choice == "2":
        inspect_budget()
    else:
        print("Not implemented yet. Use 1 or 2.")

