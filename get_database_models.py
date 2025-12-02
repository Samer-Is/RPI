"""
Get car models from database to understand what vehicles are in the fleet
"""
import pyodbc
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

def get_fleet_models():
    """Get all vehicle models from the database"""
    
    connection_string = (
        "DRIVER={SQL Server};"
        "SERVER=192.168.10.67;"
        "DATABASE=eJarDbSTGLite;"
        "Trusted_Connection=yes;"
    )
    
    query = """
    SELECT DISTINCT
        m.Id as ModelId,
        m.ModelName,
        m.Brand,
        m.CategoryName as CategoryName,
        COUNT(v.Id) as VehicleCount
    FROM Fleet.Models m
    LEFT JOIN Fleet.Vehicles v ON v.ModelId = m.Id
    GROUP BY m.Id, m.ModelName, m.Brand, m.CategoryName
    ORDER BY m.CategoryName, m.Brand, m.ModelName
    """
    
    try:
        conn = pyodbc.connect(connection_string)
        df = pd.read_sql(query, conn)
        conn.close()
        
        print("="*80)
        print("RENTY FLEET - CAR MODELS FROM DATABASE")
        print("="*80)
        print(f"Total unique models: {len(df)}")
        print()
        
        # Group by category
        for category in df['CategoryName'].dropna().unique():
            cat_df = df[df['CategoryName'] == category]
            print(f"\n{category.upper()} ({len(cat_df)} models)")
            print("-"*50)
            for _, row in cat_df.iterrows():
                vehicle_count = row['VehicleCount'] if pd.notna(row['VehicleCount']) else 0
                print(f"  {row['Brand']} {row['ModelName']} - {int(vehicle_count)} vehicles")
        
        # Save to file
        df.to_csv("data/renty_fleet_models.csv", index=False)
        print(f"\n\nSaved to data/renty_fleet_models.csv")
        
        return df
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    get_fleet_models()

