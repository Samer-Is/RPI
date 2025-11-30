-- ============================================================================
-- SQL INVESTIGATION QUERIES FOR PRICING DATA
-- ============================================================================
-- Purpose: Investigate where base prices should come from
-- Database: eJarDbSTGLite (SQL Server 2019)
-- Date: November 30, 2025
-- ============================================================================

-- ============================================================================
-- QUERY 1: Check Contract Price Distribution
-- ============================================================================
-- Purpose: Understand DailyRateAmount values and distribution

SELECT 
    'Overall Statistics' as Analysis,
    COUNT(*) as TotalContracts,
    COUNT(DISTINCT PickupBranchId) as UniqueBranches,
    COUNT(DISTINCT VehicleId) as UniqueVehicles,
    
    -- Price statistics
    MIN(DailyRateAmount) as MinPrice,
    MAX(DailyRateAmount) as MaxPrice,
    AVG(DailyRateAmount) as AvgPrice,
    STDEV(DailyRateAmount) as StdDevPrice,
    
    -- Percentiles (if supported in your SQL Server version)
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY DailyRateAmount) OVER() as P25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY DailyRateAmount) OVER() as Median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY DailyRateAmount) OVER() as P75,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY DailyRateAmount) OVER() as P90,
    
    -- Quality checks
    SUM(CASE WHEN DailyRateAmount IS NULL THEN 1 ELSE 0 END) as NullPrices,
    SUM(CASE WHEN DailyRateAmount < 50 THEN 1 ELSE 0 END) as SuspiciouslyLow,
    SUM(CASE WHEN DailyRateAmount > 2000 THEN 1 ELSE 0 END) as SuspiciouslyHigh,
    SUM(CASE WHEN DailyRateAmount BETWEEN 50 AND 2000 THEN 1 ELSE 0 END) as ReasonableRange
    
FROM [Rental].[Contract]
WHERE Start >= '2023-01-01'
    AND IsDeleted = 0;


-- ============================================================================
-- QUERY 2: Check if RentalRates Table Exists (Base Pricing)
-- ============================================================================
-- Purpose: Find if there's a rate card table with base prices

-- First, check if table exists
SELECT 
    TABLE_SCHEMA,
    TABLE_NAME,
    TABLE_TYPE
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME LIKE '%Rate%' OR TABLE_NAME LIKE '%Price%'
ORDER BY TABLE_SCHEMA, TABLE_NAME;

-- If RentalRates exists, inspect it:
-- SELECT TOP 100 * FROM [Rental].[RentalRates];


-- ============================================================================
-- QUERY 3: Inspect Contract Table Schema
-- ============================================================================
-- Purpose: Find all price/discount/promotion related fields

SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'Rental'
    AND TABLE_NAME = 'Contract'
    AND (
        COLUMN_NAME LIKE '%Price%' OR
        COLUMN_NAME LIKE '%Rate%' OR
        COLUMN_NAME LIKE '%Amount%' OR
        COLUMN_NAME LIKE '%Discount%' OR
        COLUMN_NAME LIKE '%Promo%' OR
        COLUMN_NAME LIKE '%Base%'
    )
ORDER BY ORDINAL_POSITION;


-- ============================================================================
-- QUERY 4: Sample Contract Data (Recent)
-- ============================================================================
-- Purpose: See actual contract records with all price-related fields

SELECT TOP 100
    ContractNumber,
    CAST(Start AS DATE) as StartDate,
    CAST([End] AS DATE) as EndDate,
    
    -- Price fields
    DailyRateAmount,
    MonthlyRateAmount,
    RentalRateId,
    
    -- Contract details
    PickupBranchId,
    DropoffBranchId,
    VehicleId,
    
    -- Status
    StatusId,
    FinancialStatusId,
    
    -- IDs for lookup
    CustomerId,
    BookingId,
    
    -- Duration
    DATEDIFF(day, Start, [End]) as DurationDays,
    
    -- Calculate effective daily rate if monthly rate is filled
    CASE 
        WHEN MonthlyRateAmount IS NOT NULL AND DATEDIFF(day, Start, [End]) >= 28 
        THEN MonthlyRateAmount / 30
        ELSE DailyRateAmount
    END as EffectiveDailyRate

FROM [Rental].[Contract]
WHERE Start >= '2024-01-01'
    AND IsDeleted = 0
ORDER BY CreationTime DESC;


-- ============================================================================
-- QUERY 5: Check for Discount/Promotion Fields
-- ============================================================================
-- Purpose: See if discounts are tracked

-- Check Contract table
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'Rental'
    AND TABLE_NAME = 'Contract'
ORDER BY ORDINAL_POSITION;

-- Look for related tables
SELECT 
    TABLE_SCHEMA,
    TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE (
    TABLE_NAME LIKE '%Discount%' OR
    TABLE_NAME LIKE '%Promotion%' OR
    TABLE_NAME LIKE '%Coupon%' OR
    TABLE_NAME LIKE '%Offer%'
)
ORDER BY TABLE_SCHEMA, TABLE_NAME;


-- ============================================================================
-- QUERY 6: Price Analysis by Vehicle Category
-- ============================================================================
-- Purpose: Get average prices by vehicle category (if vehicle/model data is linked)

SELECT 
    -- Need to join to Vehicle/Model tables to get category
    -- Adjust based on your schema
    v.VehicleId,
    -- m.CategoryName,  -- If available
    -- m.ModelName,     -- If available
    
    COUNT(c.Id) as ContractCount,
    AVG(c.DailyRateAmount) as AvgDailyRate,
    MIN(c.DailyRateAmount) as MinDailyRate,
    MAX(c.DailyRateAmount) as MaxDailyRate,
    STDEV(c.DailyRateAmount) as StdDevDailyRate,
    
    -- Filter reasonable range
    AVG(CASE WHEN c.DailyRateAmount BETWEEN 50 AND 2000 
             THEN c.DailyRateAmount 
             ELSE NULL END) as AvgDailyRate_Filtered

FROM [Rental].[Contract] c
LEFT JOIN [Fleet].[Vehicles] v ON c.VehicleId = v.Id
-- LEFT JOIN [Fleet].[Models] m ON v.ModelId = m.Id  -- Adjust as needed

WHERE c.Start >= '2023-01-01'
    AND c.IsDeleted = 0
    AND c.DailyRateAmount IS NOT NULL

GROUP BY v.VehicleId -- Add m.CategoryName if available
-- HAVING COUNT(*) >= 10  -- Only categories with sufficient data
ORDER BY ContractCount DESC;


-- ============================================================================
-- QUERY 7: Price Analysis by Branch
-- ============================================================================
-- Purpose: Compare prices across branches

SELECT 
    c.PickupBranchId,
    b.Name as BranchName,
    b.IsAirport,
    
    COUNT(*) as ContractCount,
    AVG(c.DailyRateAmount) as AvgPrice,
    MIN(c.DailyRateAmount) as MinPrice,
    MAX(c.DailyRateAmount) as MaxPrice,
    STDEV(c.DailyRateAmount) as StdDevPrice,
    
    -- Filtered (reasonable range)
    AVG(CASE WHEN c.DailyRateAmount BETWEEN 50 AND 2000 
             THEN c.DailyRateAmount 
             ELSE NULL END) as AvgPrice_Filtered,
    
    -- Airport premium?
    CASE WHEN b.IsAirport = 1 THEN 'Airport' ELSE 'City' END as LocationType

FROM [Rental].[Contract] c
LEFT JOIN [Rental].[Branches] b ON c.PickupBranchId = b.Id

WHERE c.Start >= '2023-01-01'
    AND c.IsDeleted = 0
    AND c.DailyRateAmount IS NOT NULL
    AND c.DailyRateAmount BETWEEN 50 AND 2000  -- Filter outliers

GROUP BY c.PickupBranchId, b.Name, b.IsAirport
HAVING COUNT(*) >= 20  -- Only branches with sufficient data
ORDER BY ContractCount DESC;


-- ============================================================================
-- QUERY 8: Time-Based Price Trends
-- ============================================================================
-- Purpose: See how prices change over time

SELECT 
    YEAR(Start) as Year,
    MONTH(Start) as Month,
    COUNT(*) as Contracts,
    AVG(DailyRateAmount) as AvgPrice,
    MIN(DailyRateAmount) as MinPrice,
    MAX(DailyRateAmount) as MaxPrice,
    STDEV(DailyRateAmount) as StdDevPrice
    
FROM [Rental].[Contract]
WHERE Start >= '2023-01-01'
    AND IsDeleted = 0
    AND DailyRateAmount BETWEEN 50 AND 2000  -- Filter outliers
    AND DailyRateAmount IS NOT NULL
    
GROUP BY YEAR(Start), MONTH(Start)
ORDER BY Year DESC, Month DESC;


-- ============================================================================
-- QUERY 9: Check Weekend vs Weekday Pricing
-- ============================================================================
-- Purpose: See if there's weekend pricing variation

SELECT 
    DATEPART(weekday, Start) as DayOfWeek,
    DATENAME(weekday, Start) as DayName,
    
    COUNT(*) as Contracts,
    AVG(DailyRateAmount) as AvgPrice,
    STDEV(DailyRateAmount) as StdDevPrice,
    
    -- Weekend indicator (adjust based on Saudi weekend = Thu/Fri)
    CASE 
        WHEN DATEPART(weekday, Start) IN (5, 6) THEN 'Weekend'  -- Thu, Fri
        ELSE 'Weekday'
    END as WeekendFlag

FROM [Rental].[Contract]
WHERE Start >= '2024-01-01'  -- Recent data
    AND IsDeleted = 0
    AND DailyRateAmount BETWEEN 50 AND 2000
    AND DailyRateAmount IS NOT NULL
    
GROUP BY DATEPART(weekday, Start), DATENAME(weekday, Start)
ORDER BY DayOfWeek;


-- ============================================================================
-- QUERY 10: Find "Base Rate" Contracts (No Discounts)
-- ============================================================================
-- Purpose: Try to isolate contracts at standard rates

-- This query attempts to find typical "base rate" contracts
-- Adjust filters based on your business logic

SELECT 
    PickupBranchId,
    -- Add vehicle category if available
    
    COUNT(*) as ContractCount,
    
    -- Use MODE (most frequent value) as likely base rate
    -- Or use 75th percentile (assuming most contracts are at or below base)
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY DailyRateAmount) OVER 
        (PARTITION BY PickupBranchId) as EstimatedBaseRate,
    
    AVG(DailyRateAmount) as AvgRate,
    MIN(DailyRateAmount) as MinRate,
    MAX(DailyRateAmount) as MaxRate

FROM [Rental].[Contract]
WHERE Start >= '2024-01-01'  -- Recent data
    AND IsDeleted = 0
    AND DailyRateAmount BETWEEN 50 AND 2000  -- Filter outliers
    AND DailyRateAmount IS NOT NULL
    
    -- Try to filter for "normal" contracts (adjust as needed)
    AND DATEDIFF(day, Start, [End]) <= 7  -- Short rentals (daily rate applies)
    -- AND StatusId = 'Completed'  -- If you want only completed contracts
    
GROUP BY PickupBranchId
HAVING COUNT(*) >= 20
ORDER BY ContractCount DESC;


-- ============================================================================
-- QUERY 11: Compare Current Hard-Coded Prices with Database
-- ============================================================================
-- Purpose: See how hard-coded dashboard prices compare to actual data

-- Current hard-coded prices (from dashboard):
-- Economy: 150 SAR
-- Compact: 180 SAR
-- Standard: 220 SAR
-- SUV Compact: 280 SAR
-- SUV Standard: 350 SAR
-- SUV Large: 500 SAR
-- Luxury Sedan: 600 SAR
-- Luxury SUV: 800 SAR

WITH HardCodedPrices AS (
    SELECT 'Economy' as Category, 150.0 as HardCodedPrice UNION ALL
    SELECT 'Compact', 180.0 UNION ALL
    SELECT 'Standard', 220.0 UNION ALL
    SELECT 'SUV Compact', 280.0 UNION ALL
    SELECT 'SUV Standard', 350.0 UNION ALL
    SELECT 'SUV Large', 500.0 UNION ALL
    SELECT 'Luxury Sedan', 600.0 UNION ALL
    SELECT 'Luxury SUV', 800.0
),
ActualPrices AS (
    SELECT 
        -- m.CategoryName,  -- If available, map to your categories
        'All Contracts' as Category,  -- Adjust based on your schema
        AVG(DailyRateAmount) as AvgActualPrice,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY DailyRateAmount) OVER() as P75ActualPrice
    FROM [Rental].[Contract]
    WHERE Start >= '2024-01-01'
        AND IsDeleted = 0
        AND DailyRateAmount BETWEEN 50 AND 2000
    -- GROUP BY m.CategoryName
)
SELECT 
    h.Category,
    h.HardCodedPrice,
    a.AvgActualPrice,
    a.P75ActualPrice,
    (a.AvgActualPrice - h.HardCodedPrice) as Difference_Avg,
    ((a.AvgActualPrice - h.HardCodedPrice) / h.HardCodedPrice * 100) as PctDiff_Avg
FROM HardCodedPrices h
LEFT JOIN ActualPrices a ON h.Category = a.Category
ORDER BY h.HardCodedPrice;


-- ============================================================================
-- QUERY 12: Booking vs Contract Price Check
-- ============================================================================
-- Purpose: Check if Booking table has different pricing

-- First, check if Bookings table has price fields
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'Rental'
    AND TABLE_NAME = 'Bookings'
    AND (
        COLUMN_NAME LIKE '%Price%' OR
        COLUMN_NAME LIKE '%Rate%' OR
        COLUMN_NAME LIKE '%Amount%'
    );

-- If price fields exist in Bookings:
/*
SELECT TOP 100
    b.BookingNumber,
    b.BookingDate,
    -- b.QuotedPrice,  -- Adjust field names
    c.DailyRateAmount as ContractPrice,
    -- (c.DailyRateAmount - b.QuotedPrice) as PriceDifference
FROM [Rental].[Bookings] b
LEFT JOIN [Rental].[Contract] c ON b.Id = c.BookingId
WHERE b.BookingDate >= '2024-01-01'
ORDER BY b.BookingDate DESC;
*/


-- ============================================================================
-- QUERY 13: Check for Rate Card / Price List Tables
-- ============================================================================
-- Purpose: Find official rate card

-- Search for any tables that might contain base rates
SELECT 
    t.TABLE_SCHEMA,
    t.TABLE_NAME,
    c.COLUMN_NAME,
    c.DATA_TYPE
FROM INFORMATION_SCHEMA.TABLES t
JOIN INFORMATION_SCHEMA.COLUMNS c 
    ON t.TABLE_SCHEMA = c.TABLE_SCHEMA 
    AND t.TABLE_NAME = c.TABLE_NAME
WHERE (
    t.TABLE_NAME LIKE '%Rate%' OR
    t.TABLE_NAME LIKE '%Price%' OR
    t.TABLE_NAME LIKE '%Tariff%' OR
    t.TABLE_NAME LIKE '%Fee%'
)
    AND c.COLUMN_NAME LIKE '%Amount%' OR c.COLUMN_NAME LIKE '%Price%'
ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION;


-- ============================================================================
-- EXECUTION GUIDE
-- ============================================================================
/*
RUN IN THIS ORDER:

1. Query 1: Get overall price statistics
2. Query 2: Check if RentalRates table exists
3. Query 3: See all price-related fields in Contract
4. Query 4: Sample recent contracts
5. Query 7: Price by branch (very important!)
6. Query 8: Price trends over time
7. Query 10: Estimate base rates
8. Query 11: Compare with hard-coded prices

SAVE RESULTS TO EXCEL for analysis.

KEY QUESTIONS TO ANSWER:
- What is the median DailyRateAmount? (Compare with hard-coded 150-800 SAR)
- Is there a RentalRates table with base pricing?
- Are there discount/promotion fields?
- Do airport branches charge more? (Compare IsAirport = 1 vs 0)
- How much do prices vary?

*/

