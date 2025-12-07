"""
Module to read competitor prices from daily stored data
Replaces live API calls in the dashboard
"""
import json
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to stored data file - use absolute path relative to this script's location
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_FILE = SCRIPT_DIR / "data" / "competitor_prices" / "daily_competitor_prices.json"

# Cache the loaded data in memory
_cached_data = None
_cache_timestamp = None

def clear_cache():
    """Clear the in-memory cache to force fresh data load"""
    global _cached_data, _cache_timestamp
    _cached_data = None
    _cache_timestamp = None
    logger.info("Competitor price cache cleared")

def load_stored_data(force_reload=False) -> Optional[Dict]:
    """
    Load competitor price data from stored JSON file
    Uses in-memory cache to avoid repeated file reads
    
    Set force_reload=True to bypass cache and load fresh from file
    """
    global _cached_data, _cache_timestamp
    
    # Return cached data if available and not forcing reload
    if _cached_data is not None and not force_reload:
        return _cached_data
    
    try:
        if not DATA_FILE.exists():
            logger.error(f"Competitor price file not found: {DATA_FILE}")
            return None
            
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            _cached_data = json.load(f)
            _cache_timestamp = datetime.now()
        
        logger.info(f"Loaded competitor prices from: {DATA_FILE}")
        logger.info(f"Data scraped at: {_cached_data.get('scrape_timestamp', 'Unknown')}")
        
        return _cached_data
        
    except FileNotFoundError:
        logger.error(f"Competitor price file not found: {DATA_FILE}")
        logger.error("Please run 'python daily_competitor_scraper.py' first")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing competitor price file: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error loading competitor prices: {str(e)}")
        return None

def get_competitor_prices_for_branch_category(branch_name: str, category: str) -> Dict:
    """
    Get competitor prices for a specific branch and category from stored data
    
    Returns:
    {
        'avg_price': float or None,
        'min_price': float or None,
        'max_price': float or None,
        'competitors': list of dicts,
        'competitor_count': int
    }
    """
    data = load_stored_data()
    
    if not data:
        return {
            'avg_price': None,
            'min_price': None,
            'max_price': None,
            'competitors': [],
            'competitor_count': 0
        }
    
    # Try exact match first
    branch_data = data.get('branches', {}).get(branch_name)
    
    # If not found, try fuzzy match
    if not branch_data:
        for stored_branch, stored_data in data.get('branches', {}).items():
            if branch_name.lower() in stored_branch.lower() or stored_branch.lower() in branch_name.lower():
                branch_data = stored_data
                logger.info(f"Fuzzy matched '{branch_name}' to '{stored_branch}'")
                break
    
    if not branch_data:
        logger.warning(f"Branch '{branch_name}' not found in stored data")
        return {
            'avg_price': None,
            'min_price': None,
            'max_price': None,
            'competitors': [],
            'competitor_count': 0
        }
    
    # Get category data
    categories = branch_data.get('categories', {})
    category_data = categories.get(category)
    
    if not category_data:
        logger.warning(f"Category '{category}' not found for branch '{branch_name}'")
        return {
            'avg_price': None,
            'min_price': None,
            'max_price': None,
            'competitors': [],
            'competitor_count': 0
        }
    
    # Extract and return data
    competitors = category_data.get('competitors', [])
    competitor_prices = [c['Competitor_Price'] for c in competitors] if competitors else []
    
    return {
        'avg_price': category_data.get('avg_price'),
        'min_price': min(competitor_prices) if competitor_prices else None,
        'max_price': max(competitor_prices) if competitor_prices else None,
        'competitors': competitors,
        'competitor_count': len(competitors)
    }

def get_data_freshness() -> Dict:
    """
    Get information about when the data was last updated
    """
    data = load_stored_data()
    
    if not data:
        return {
            'available': False,
            'message': 'No data available'
        }
    
    scrape_timestamp = data.get('scrape_timestamp')
    
    if scrape_timestamp:
        scrape_time = datetime.fromisoformat(scrape_timestamp)
        age_hours = (datetime.now() - scrape_time).total_seconds() / 3600
        
        if age_hours < 24:
            status = "Fresh"
        elif age_hours < 48:
            status = "Stale (needs update)"
        else:
            status = "Very old (update required)"
        
        return {
            'available': True,
            'scrape_timestamp': scrape_timestamp,
            'age_hours': round(age_hours, 1),
            'status': status,
            'message': f"Data is {age_hours:.1f} hours old - {status}"
        }
    else:
        return {
            'available': True,
            'message': 'Data available but timestamp unknown'
        }

def get_available_branches() -> list:
    """Get list of branches available in stored data"""
    data = load_stored_data()
    
    if not data:
        return []
    
    return list(data.get('branches', {}).keys())

def get_available_categories_for_branch(branch_name: str) -> list:
    """Get list of categories with data for a specific branch"""
    data = load_stored_data()
    
    if not data:
        return []
    
    branch_data = data.get('branches', {}).get(branch_name)
    
    if not branch_data:
        return []
    
    categories = branch_data.get('categories', {})
    
    # Return categories that have at least one competitor
    return [
        cat for cat, cat_data in categories.items()
        if cat_data.get('competitors')
    ]
