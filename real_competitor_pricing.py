"""
REAL Competitor Pricing System - NO SIMULATIONS
Loads manually validated competitor prices from CSV
"""
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List

class RealCompetitorPricing:
    """
    Load and serve REAL competitor prices from manual validation
    """
    
    def __init__(self, prices_file='manual_competitor_prices.csv'):
        self.prices_file = prices_file
        self.prices_df = None
        self.load_prices()
    
    def load_prices(self):
        """Load competitor prices from CSV"""
        if os.path.exists(self.prices_file):
            try:
                # Read CSV, skip comment lines
                self.prices_df = pd.read_csv(
                    self.prices_file,
                    comment='#',
                    parse_dates=['Date']
                )
                print(f"[OK] Loaded {len(self.prices_df)} real competitor prices from {self.prices_file}")
            except Exception as e:
                print(f"[WARNING] Could not load {self.prices_file}: {e}")
                self.prices_df = pd.DataFrame()
        else:
            print(f"[WARNING] {self.prices_file} not found. No real competitor data available.")
            self.prices_df = pd.DataFrame()
    
    def get_live_prices(
        self,
        category: str,
        branch_name: str,
        date: datetime,
        **kwargs  # Ignore event flags for now
    ) -> Dict:
        """
        Get REAL competitor prices if available, otherwise return warning
        """
        if self.prices_df is None or len(self.prices_df) == 0:
            return {
                'competitors': [],
                'avg_price': None,
                'competitor_count': 0,
                'last_updated': None,
                'is_live': False,
                'warning': 'NO REAL COMPETITOR DATA AVAILABLE - Manual validation required',
                'location': branch_name,
                'category': category
            }
        
        # Try to find matching prices
        # For simplicity, match by category and general location
        location_key = self._simplify_location(branch_name)
        
        matches = self.prices_df[
            (self.prices_df['Category'].str.lower() == category.lower()) &
            (self.prices_df['Location'].str.contains(location_key, case=False, na=False))
        ]
        
        if len(matches) == 0:
            # Try without location match
            matches = self.prices_df[
                self.prices_df['Category'].str.lower() == category.lower()
            ]
        
        if len(matches) == 0:
            return {
                'competitors': [],
                'avg_price': None,
                'competitor_count': 0,
                'last_updated': None,
                'is_live': False,
                'warning': f'No validated prices for {category} at {branch_name}',
                'location': branch_name,
                'category': category
            }
        
        # Build competitor list
        competitors = []
        for _, row in matches.iterrows():
            competitors.append({
                'Competitor_Name': row['Competitor'],
                'Competitor_Price': int(row['ActualPrice']),
                'Competitor_Category': row['Category'],
                'Date': row['Date'].strftime('%Y-%m-%d'),
                'Source': row['Source'],
                'Confidence': 100,  # Real data = 100% confidence
                'Notes': row.get('Notes', '')
            })
        
        avg_price = matches['ActualPrice'].mean()
        
        return {
            'competitors': competitors,
            'avg_price': avg_price,
            'competitor_count': len(competitors),
            'last_updated': matches['Date'].max().isoformat(),
            'location': branch_name,
            'category': category,
            'is_live': True,
            'data_source': 'MANUAL_VALIDATION'
        }
    
    def _simplify_location(self, branch_name: str) -> str:
        """Extract key location word from branch name"""
        branch_lower = branch_name.lower()
        if 'riyadh' in branch_lower:
            return 'riyadh'
        elif 'jeddah' in branch_lower:
            return 'jeddah'
        elif 'dammam' in branch_lower:
            return 'dammam'
        elif 'mecca' in branch_lower or 'makkah' in branch_lower:
            return 'mecca'
        elif 'medina' in branch_lower:
            return 'medina'
        else:
            return branch_name.split()[0]  # First word


# Simple function for dashboard integration (compatible with old API)
def get_competitor_prices_for_dashboard(
    category: str,
    branch_name: str,
    date: datetime,
    **event_flags
) -> Dict:
    """
    Get REAL competitor prices (manual validation)
    Compatible with existing dashboard API
    """
    scraper = RealCompetitorPricing()
    return scraper.get_live_prices(category, branch_name, date, **event_flags)


def compare_with_competitors(renty_price: float, comp_stats: Dict) -> Dict:
    """
    Compare Renty price with competitors (unchanged from original)
    """
    if not comp_stats or not comp_stats.get('avg_price'):
        return {
            'cheaper': False,
            'more_expensive': False,
            'difference': 0,
            'percentage': 0
        }
    
    avg_comp = comp_stats['avg_price']
    diff = renty_price - avg_comp
    pct = (diff / avg_comp * 100) if avg_comp > 0 else 0
    
    return {
        'cheaper': diff < 0,
        'more_expensive': diff > 0,
        'difference': diff,
        'percentage': pct
    }


if __name__ == "__main__":
    # Test
    print("="*80)
    print("REAL COMPETITOR PRICING SYSTEM TEST")
    print("="*80)
    
    scraper = RealCompetitorPricing()
    
    result = scraper.get_live_prices(
        category="Economy",
        branch_name="Riyadh Airport",
        date=datetime.now()
    )
    
    print("\nResult:")
    print(f"  Category: {result['category']}")
    print(f"  Location: {result['location']}")
    print(f"  Competitors Found: {result['competitor_count']}")
    print(f"  Average Price: {result.get('avg_price', 'N/A')}")
    
    if 'warning' in result:
        print(f"\n  WARNING: {result['warning']}")
        print("\n  TO ADD REAL PRICES:")
        print("  1. Open manual_competitor_prices.csv")
        print("  2. Add rows with real prices from competitor websites")
        print("  3. Save and reload")
    else:
        print(f"\n  Data Source: {result.get('data_source', 'Unknown')}")
        for comp in result['competitors']:
            print(f"  - {comp['Competitor_Name']}: {comp['Competitor_Price']} SAR")
    
    print("\n" + "="*80)

