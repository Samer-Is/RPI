"""
Daily Competitor Price Scraper
Fetches all competitor prices for all branches and categories from Booking.com API
Stores in a single JSON file for dashboard consumption
Run this script once daily (e.g., via scheduled task at midnight)
"""
import json
from datetime import datetime, timedelta
from booking_com_api import get_api_instance
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# All branches to scrape
BRANCHES = [
    "King Khalid Airport - Riyadh",
    "Olaya District - Riyadh",
    "King Abdulaziz Airport - Jeddah",
    "Jeddah City Center",
    "King Fahd Airport - Dammam",
    "Al Khobar Business District",
    "Mecca City Center",
    "Medina Downtown"
]

# All categories
CATEGORIES = [
    "Economy",
    "Compact",
    "Standard",
    "SUV Compact",
    "SUV Standard",
    "SUV Large",
    "Luxury Sedan",
    "Luxury SUV"
]

def scrape_all_competitor_prices():
    """
    Scrape competitor prices for all branches and categories
    Returns a dictionary with all data
    """
    api = get_api_instance()
    
    # Use tomorrow's date (API doesn't accept past dates)
    scrape_date = datetime.now() + timedelta(days=1)
    
    logger.info("="*70)
    logger.info(f"Starting daily competitor price scrape")
    logger.info(f"Scrape date: {scrape_date.strftime('%Y-%m-%d')}")
    logger.info(f"Branches: {len(BRANCHES)}")
    logger.info(f"Categories: {len(CATEGORIES)}")
    logger.info("="*70)
    
    all_data = {
        "scrape_timestamp": datetime.now().isoformat(),
        "scrape_date": scrape_date.strftime('%Y-%m-%d'),
        "branches": {}
    }
    
    success_count = 0
    fail_count = 0
    
    for branch in BRANCHES:
        logger.info(f"\nScraping: {branch}")
        
        try:
            # Get all category prices for this branch (single API call)
            branch_data = api.get_competitor_prices_for_dashboard(branch, scrape_date)
            
            all_data["branches"][branch] = {
                "categories": branch_data,
                "last_updated": datetime.now().isoformat()
            }
            
            # Count competitors found
            total_competitors = sum(
                len(cat_data.get('competitors', [])) 
                for cat_data in branch_data.values()
            )
            
            logger.info(f"  ✓ Success: {len(branch_data)} categories, {total_competitors} total competitors")
            success_count += 1
            
        except Exception as e:
            logger.error(f"  ✗ Failed: {str(e)}")
            all_data["branches"][branch] = {
                "categories": {},
                "last_updated": datetime.now().isoformat(),
                "error": str(e)
            }
            fail_count += 1
    
    logger.info("\n" + "="*70)
    logger.info(f"Scrape complete!")
    logger.info(f"Success: {success_count}/{len(BRANCHES)} branches")
    logger.info(f"Failed: {fail_count}/{len(BRANCHES)} branches")
    logger.info("="*70)
    
    return all_data

def save_to_file(data, filepath="data/competitor_prices/daily_competitor_prices.json"):
    """Save scraped data to JSON file"""
    import os
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\nData saved to: {filepath}")
    
    # Calculate file size
    file_size = os.path.getsize(filepath) / 1024  # KB
    logger.info(f"File size: {file_size:.2f} KB")

def main():
    """Main execution"""
    try:
        # Scrape all data
        data = scrape_all_competitor_prices()
        
        # Save to file
        save_to_file(data)
        
        logger.info("\n✓ Daily competitor price update complete!")
        logger.info(f"Next update should run: {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M')}")
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Daily scrape FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
