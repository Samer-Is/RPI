"""
Get the LAST (most recent) rental price per category from the database
This will be used as the base price in the dashboard
"""
import pyodbc
import pandas as pd
from datetime import datetime
import config

def get_connection():
    """Create database connection"""
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={config.DB_CONFIG['server']};"
        f"DATABASE={config.DB_CONFIG['database']};"
        f"Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

def get_latest_rental_prices():
    """
    Get the most recent rental price for each category
    Uses the LAST rental (most recent date) as the base price
    """
    conn = get_connection()
    
    # Query to get the most recent rental per category
    # We'll look at the training data date range (up to Nov 18, 2025)
    query = """
    WITH LatestRentals AS (
        SELECT 
            m.CategoryName,
            co.DailyRateAmount,
            co.[Start],
            ROW_NUMBER() OVER (PARTITION BY m.CategoryName ORDER BY co.[Start] DESC) as rn
        FROM Rental.[Contract] co
        INNER JOIN Fleet.Vehicles v ON co.VehicleId = v.Id
        INNER JOIN Fleet.Models m ON v.ModelId = m.Id
        WHERE co.[Start] <= '2025-11-18'
        AND co.DailyRateAmount IS NOT NULL
        AND co.DailyRateAmount > 0
        AND co.IsDeleted = 0
    )
    SELECT 
        CategoryName,
        DailyRateAmount as LastRentalPrice,
        [Start] as LastRentalDate
    FROM LatestRentals
    WHERE rn = 1
    ORDER BY CategoryName
    """
    
    print("Querying database for most recent rental prices per category...")
    print(f"Date range: Up to 2025-11-18")
    print("="*70)
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df

def map_to_dashboard_categories(df):
    """
    Map database categories to dashboard categories
    """
    # Category mapping from database to dashboard
    category_mapping = {
        "Economy": "Economy",
        "Compact": "Compact",
        "Standard": "Standard",
        "Intermediate": "Standard",
        "Full Size": "Standard",
        "Compact SUV": "SUV Compact",
        "Small SUV": "SUV Compact",
        "Standard SUV": "SUV Standard",
        "Medium SUV": "SUV Standard",
        "Large SUV": "SUV Large",
        "Full-size SUV": "SUV Large",
        "Luxury Car": "Luxury Sedan",
        "Premium Car": "Luxury Sedan",
        "Luxury Sedan": "Luxury Sedan",
        "Luxury SUV": "Luxury SUV",
        "Premium SUV": "Luxury SUV"
    }
    
    # Map and aggregate if multiple DB categories map to one dashboard category
    results = {}
    
    for _, row in df.iterrows():
        db_cat = row['CategoryName']
        dashboard_cat = category_mapping.get(db_cat, db_cat)
        
        if dashboard_cat not in results:
            results[dashboard_cat] = {
                'price': row['LastRentalPrice'],
                'date': row['LastRentalDate'],
                'db_category': db_cat
            }
        else:
            # If we have multiple, use the most recent
            if row['LastRentalDate'] > results[dashboard_cat]['date']:
                results[dashboard_cat] = {
                    'price': row['LastRentalPrice'],
                    'date': row['LastRentalDate'],
                    'db_category': db_cat
                }
    
    return results

def main():
    """Main execution"""
    try:
        # Get data from database
        df = get_latest_rental_prices()
        
        if df.empty:
            print("ERROR: No rental data found!")
            return False
        
        print(f"\nFound {len(df)} categories with rental data\n")
        print("Database Results:")
        print("="*70)
        for _, row in df.iterrows():
            print(f"{row['CategoryName']:20} {row['LastRentalPrice']:8.2f} SAR/day  (Date: {row['LastRentalDate']})")
        
        # Map to dashboard categories
        dashboard_prices = map_to_dashboard_categories(df)
        
        print("\n\nMapped to Dashboard Categories:")
        print("="*70)
        
        # Expected dashboard categories
        expected_categories = [
            "Economy", "Compact", "Standard", 
            "SUV Compact", "SUV Standard", "SUV Large",
            "Luxury Sedan", "Luxury SUV"
        ]
        
        base_prices = {}
        for cat in expected_categories:
            if cat in dashboard_prices:
                info = dashboard_prices[cat]
                base_prices[cat] = round(info['price'], 2)
                print(f"{cat:20} {info['price']:8.2f} SAR/day  (Date: {info['date']}, from DB: {info['db_category']})")
            else:
                print(f"{cat:20} NO DATA FOUND")
                base_prices[cat] = None
        
        # Generate Python code for dashboard_manager.py
        print("\n\n" + "="*70)
        print("COPY THIS INTO dashboard_manager.py:")
        print("="*70)
        print("\nVEHICLE_CATEGORIES = {")
        
        category_examples = {
            "Economy": "Hyundai Accent, Kia Picanto, Nissan Sunny",
            "Compact": "Toyota Yaris, Hyundai Elantra, Kia Cerato",
            "Standard": "Toyota Camry, Hyundai Sonata, Nissan Altima",
            "SUV Compact": "Hyundai Tucson, Nissan Qashqai, Kia Sportage",
            "SUV Standard": "Toyota RAV4, Nissan X-Trail, Hyundai Santa Fe",
            "SUV Large": "Toyota Land Cruiser, Nissan Patrol, Chevrolet Tahoe",
            "Luxury Sedan": "BMW 5 Series, Mercedes E-Class, Audi A6",
            "Luxury SUV": "BMW X5, Mercedes GLE, Audi Q7"
        }
        
        category_icons = {
            "Economy": "🚗",
            "Compact": "🚙",
            "Standard": "🚘",
            "SUV Compact": "🚐",
            "SUV Standard": "🚙",
            "SUV Large": "🚐",
            "Luxury Sedan": "🚗",
            "Luxury SUV": "🚙"
        }
        
        for cat in expected_categories:
            price = base_prices.get(cat, 150.0)  # Fallback if no data
            if price is None:
                price = 150.0  # Default fallback
            
            print(f'    "{cat}": {{')
            print(f'        "examples": "{category_examples[cat]}",')
            print(f'        "base_price": {price},')
            print(f'        "icon": "{category_icons[cat]}"')
            print(f'    }},')
        
        print("}")
        print("\n" + "="*70)
        
        # Save to file
        with open('latest_base_prices_output.txt', 'w') as f:
            f.write("Latest Rental Prices per Category\n")
            f.write("="*70 + "\n\n")
            f.write("Database Results:\n")
            f.write("-"*70 + "\n")
            for _, row in df.iterrows():
                f.write(f"{row['CategoryName']:20} {row['LastRentalPrice']:8.2f} SAR/day  (Date: {row['LastRentalDate']})\n")
            
            f.write("\n\nDashboard Base Prices:\n")
            f.write("-"*70 + "\n")
            for cat in expected_categories:
                if cat in dashboard_prices:
                    info = dashboard_prices[cat]
                    f.write(f"{cat:20} {info['price']:8.2f} SAR/day\n")
                else:
                    f.write(f"{cat:20} NO DATA\n")
        
        print("\n✓ Results saved to: latest_base_prices_output.txt")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

