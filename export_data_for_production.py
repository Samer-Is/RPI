"""
Export Database Data for Production Deployment

Run this script ONCE to export VehicleHistory data to local CSV.
After export, the dashboard can run WITHOUT database connection.

Usage:
    python export_data_for_production.py
"""

import pandas as pd
import pyodbc
from datetime import datetime, timedelta
from pathlib import Path
import config

# Output directory
OUTPUT_DIR = Path('data')
OUTPUT_DIR.mkdir(exist_ok=True)

def export_vehicle_history():
    """Export current utilization per branch to local CSV."""
    print("="*60)
    print("EXPORTING VEHICLE HISTORY FOR PRODUCTION")
    print("="*60)
    
    try:
        # Connect to database
        conn_str = (
            f"DRIVER={config.DB_CONFIG['driver']};"
            f"SERVER={config.DB_CONFIG['server']};"
            f"DATABASE={config.DB_CONFIG['database']};"
            f"Trusted_Connection={config.DB_CONFIG['trusted_connection']};"
        )
        conn = pyodbc.connect(conn_str)
        print("[OK] Connected to database")
        
        # Query: Get latest status per vehicle per branch
        query = """
        WITH LatestStatus AS (
            SELECT 
                vh.VehicleId,
                vh.BranchId,
                vh.StatusId,
                vh.OperationDateTime,
                ROW_NUMBER() OVER (PARTITION BY vh.VehicleId ORDER BY vh.OperationDateTime DESC) as rn
            FROM Fleet.VehicleHistory vh
            WHERE vh.OperationDateTime >= DATEADD(day, -60, GETDATE())
        )
        SELECT 
            BranchId,
            COUNT(*) as total_vehicles,
            SUM(CASE WHEN StatusId IN (141, 144, 146, 147, 154, 155) THEN 1 ELSE 0 END) as rented_vehicles,
            SUM(CASE WHEN StatusId = 140 THEN 1 ELSE 0 END) as available_vehicles
        FROM LatestStatus
        WHERE rn = 1
        GROUP BY BranchId
        ORDER BY BranchId
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Calculate utilization percentage
        df['utilization_pct'] = (df['rented_vehicles'] / df['total_vehicles'] * 100).round(1)
        
        # Add export timestamp
        df['export_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save to CSV
        output_file = OUTPUT_DIR / 'vehicle_history_local.csv'
        df.to_csv(output_file, index=False)
        
        print(f"[OK] Exported {len(df)} branches to {output_file}")
        print("\nData preview:")
        print(df.to_string())
        
        print("\n" + "="*60)
        print("EXPORT COMPLETE!")
        print("="*60)
        print(f"\nFile saved: {output_file}")
        print("\nYou can now deploy without database connection.")
        print("The dashboard will use this local file for utilization data.")
        
        return df
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return None


if __name__ == "__main__":
    export_vehicle_history()

