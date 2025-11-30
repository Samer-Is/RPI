"""
Check database schema to find correct column names
"""
import pyodbc
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

def check_tables():
    """Check available tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("Checking Rental.Contract table structure:")
    print("="*70)
    
    # Get column names from Contract table
    cursor.execute("""
        SELECT TOP 1 * FROM Rental.[Contract]
    """)
    
    columns = [column[0] for column in cursor.description]
    print("\nRental.Contract columns:")
    for col in columns:
        print(f"  - {col}")
    
    print("\n" + "="*70)
    print("Checking Fleet.Vehicles table structure:")
    print("="*70)
    
    # Get column names from Vehicles table
    cursor.execute("""
        SELECT TOP 1 * FROM Fleet.Vehicles
    """)
    
    columns = [column[0] for column in cursor.description]
    print("\nFleet.Vehicles columns:")
    for col in columns:
        print(f"  - {col}")
    
    print("\n" + "="*70)
    print("Sample data from Contract:")
    print("="*70)
    
    # Get sample data
    cursor.execute("""
        SELECT TOP 5 
            ContractID,
            StartDate,
            DailyRate
        FROM Rental.[Contract]
        WHERE DailyRate IS NOT NULL
        AND StartDate <= '2025-11-18'
        ORDER BY StartDate DESC
    """)
    
    for row in cursor.fetchall():
        print(f"  ContractID: {row[0]}, Date: {row[1]}, Rate: {row[2]}")
    
    conn.close()

if __name__ == "__main__":
    try:
        check_tables()
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

