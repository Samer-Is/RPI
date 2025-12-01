"""
Daily Kayak Competitor Price Scraper
Fetches all competitor prices for all branches and categories once daily
Stores results in JSON file for fast dashboard access
"""
import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from kayak_api import get_kayak_client

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

# Output file path
OUTPUT_FILE = Path("data/competitor_prices/daily_kayak_prices.json")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Branch definitions (from dashboard_manager.py)
BRANCHES = {
    "King Khalid Airport - Riyadh": {"city": "Riyadh", "name": "King Khalid Airport - Riyadh"},
    "Olaya District - Riyadh": {"city": "Riyadh", "name": "Olaya District - Riyadh"},
    "King Fahd Airport - Dammam": {"city": "Dammam", "name": "King Fahd Airport - Dammam"},
    "King Abdulaziz Airport - Jeddah": {"city": "Jeddah", "name": "King Abdulaziz Airport - Jeddah"},
    "Al Khobar Business District": {"city": "Al Khobar", "name": "Al Khobar Business District"},
    "Mecca City Center": {"city": "Mecca", "name": "Mecca City Center"},
    "Medina Downtown": {"city": "Medina", "name": "Medina Downtown"},
    "Jeddah City Center": {"city": "Jeddah", "name": "Jeddah City Center"}
}

def scrape_all_branches():
    """
    Scrape competitor prices from Kayak for all branches and categories
    """
    scrape_date = date.today()
    tomorrow = scrape_date + timedelta(days=1)
    day_after = tomorrow + timedelta(days=2)
    
    logger.info("="*70)
    logger.info("Starting daily Kayak competitor price scrape")
    logger.info(f"Scrape date: {scrape_date}")
    logger.info(f"Rental period: {tomorrow} to {day_after} (2 days)")
    logger.info(f"Branches: {len(BRANCHES)}")
    logger.info("="*70)
    
    kayak_client = get_kayak_client()
    
    # Store results
    results = {
        "scrape_timestamp": datetime.now().isoformat(),
        "scrape_date": scrape_date.isoformat(),
        "rental_period": {
            "pickup": tomorrow.isoformat(),
            "dropoff": day_after.isoformat(),
            "days": 2
        },
        "branches": {}
    }
    
    successful_branches = 0
    failed_branches = []
    
    for branch_name, branch_info in BRANCHES.items():
        logger.info(f"\nScraping: {branch_name}")
        
        try:
            # Get all categories for this branch
            category_prices = kayak_client.search_cars(branch_name, tomorrow, day_after)
            
            # Format results
            branch_data = {
                "categories": {},
                "last_updated": datetime.now().isoformat(),
                "location": {
                    "city": branch_info.get("city", ""),
                    "name": branch_info.get("name", "")
                }
            }
            
            total_competitors = 0
            
            for category, prices in category_prices.items():
                if prices:
                    # Format competitor data
                    competitors = [
                        {
                            "Competitor_Name": p['supplier'],
                            "Competitor_Price": p['price_per_day'],
                            "Date": datetime.now().strftime('%Y-%m-%d %H:%M'),
                            "Vehicle": p['vehicle']
                        }
                        for p in prices
                    ]
                    
                    prices_list = [p['price_per_day'] for p in prices]
                    
                    branch_data["categories"][category] = {
                        "avg_price": round(sum(prices_list) / len(prices_list), 2),
                        "min_price": min(prices_list),
                        "max_price": max(prices_list),
                        "competitors": competitors
                    }
                    
                    total_competitors += len(competitors)
                else:
                    # Empty category
                    branch_data["categories"][category] = {
                        "avg_price": None,
                        "min_price": None,
                        "max_price": None,
                        "competitors": []
                    }
            
            results["branches"][branch_name] = branch_data
            successful_branches += 1
            
            logger.info(f"  Success: {len([c for c in branch_data['categories'].values() if c['competitors']])} categories, {total_competitors} total competitors")
            
        except Exception as e:
            logger.error(f"  Failed to scrape {branch_name}: {str(e)}")
            failed_branches.append(branch_name)
            
            # Add empty data for failed branch
            results["branches"][branch_name] = {
                "categories": {cat: {"avg_price": None, "min_price": None, "max_price": None, "competitors": []} 
                              for cat in ["Economy", "Compact", "Standard", "SUV Compact", "SUV Standard", "SUV Large", "Luxury Sedan", "Luxury SUV"]},
                "last_updated": datetime.now().isoformat(),
                "location": {"city": branch_info.get("city", ""), "name": branch_info.get("name", "")},
                "error": str(e)
            }
    
    # Save results to JSON
    logger.info("\n" + "="*70)
    logger.info("Scrape complete!")
    logger.info(f"Success: {successful_branches}/{len(BRANCHES)} branches")
    logger.info(f"Failed: {len(failed_branches)}/{len(BRANCHES)} branches")
    if failed_branches:
        logger.info(f"Failed branches: {', '.join(failed_branches)}")
    logger.info("="*70)
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        file_size_kb = OUTPUT_FILE.stat().st_size / 1024
        logger.info(f"\nData saved to: {OUTPUT_FILE}")
        logger.info(f"File size: {file_size_kb:.2f} KB")
        
        # Calculate next update time (24 hours from now)
        next_update = datetime.now() + timedelta(days=1)
        logger.info(f"\nNext update should run: {next_update.strftime('%Y-%m-%d %H:%M')}")
        
        print(f"\n[OK] Daily Kayak competitor price update complete!")
        
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
        raise

if __name__ == "__main__":
    scrape_all_branches()

