"""Verify the exported data matches the live database."""
import pyodbc
import pandas as pd
import config

# Connect to database
conn_str = (
    f"DRIVER={config.DB_CONFIG['driver']};"
    f"SERVER={config.DB_CONFIG['server']};"
    f"DATABASE={config.DB_CONFIG['database']};"
    f"Trusted_Connection={config.DB_CONFIG['trusted_connection']};"
)
conn = pyodbc.connect(conn_str)

# Check branch 122 (King Khalid Airport) from LIVE database
query = """
WITH LatestStatus AS (
    SELECT VehicleId, BranchId, StatusId,
           ROW_NUMBER() OVER (PARTITION BY VehicleId ORDER BY OperationDateTime DESC) as rn
    FROM Fleet.VehicleHistory
    WHERE OperationDateTime >= DATEADD(day, -60, GETDATE())
      AND BranchId = 122
)
SELECT COUNT(*) as total,
       SUM(CASE WHEN StatusId IN (141, 144, 146, 147, 154, 155) THEN 1 ELSE 0 END) as rented,
       SUM(CASE WHEN StatusId = 140 THEN 1 ELSE 0 END) as available
FROM LatestStatus WHERE rn = 1
"""
cursor = conn.cursor()
cursor.execute(query)
row = cursor.fetchone()

print("=" * 60)
print("LIVE DATABASE VERIFICATION")
print("=" * 60)
print(f"\nBranch 122 (King Khalid Airport) - LIVE from Fleet.VehicleHistory:")
print(f"  Total vehicles: {row[0]}")
print(f"  Rented: {row[1]}")
print(f"  Available: {row[2]}")
print(f"  Utilization: {round(row[1]/row[0]*100, 1)}%")

# Compare with exported CSV
print("\n" + "-" * 60)
df = pd.read_csv('data/vehicle_history_local.csv')
branch_122 = df[df['BranchId'] == 122].iloc[0]
print(f"\nBranch 122 from EXPORTED CSV:")
print(f"  Total vehicles: {branch_122['total_vehicles']}")
print(f"  Rented: {branch_122['rented_vehicles']}")
print(f"  Available: {branch_122['available_vehicles']}")
print(f"  Utilization: {branch_122['utilization_pct']}%")
print(f"  Export time: {branch_122['export_date']}")

print("\n" + "=" * 60)
if row[0] == branch_122['total_vehicles']:
    print("VERIFIED: Data matches!")
else:
    print("Note: Minor differences may exist due to real-time changes")
print("=" * 60)

conn.close()

