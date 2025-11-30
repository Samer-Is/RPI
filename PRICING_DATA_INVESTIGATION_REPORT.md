# 🔍 **CRITICAL INVESTIGATION REPORT: Pricing Data & Competitor Intelligence**

**Investigation Date:** November 30, 2025  
**Investigated By:** AI Development Team  
**Status:** 🔴 **CRITICAL FINDINGS - REQUIRES IMMEDIATE ATTENTION**

---

## 📋 **Executive Summary**

**User's Questions:**
1. **Where do base prices come from? Are they from contracts/actual bookings?**
2. **How accurate is the live competitor pricing scraper?**

**Key Findings:**
- ❌ **Base prices are HARD-CODED, not from database**
- ❌ **Competitor pricing is 100% SIMULATED, not scraped**
- ⚠️ **Historical contract prices (DailyRateAmount) exist but are NOT used**
- ⚠️ **Model predicts DEMAND (bookings count), NOT prices**

---

## 🔴 **CRITICAL FINDING #1: Base Prices Are Hard-Coded**

### **Current Implementation:**

**File:** `dashboard_manager.py` (Lines 100-142)

```python
VEHICLE_CATEGORIES = {
    "Economy": {"base_price": 150.0},       # ← HARD-CODED
    "Compact": {"base_price": 180.0},       # ← HARD-CODED
    "Standard": {"base_price": 220.0},      # ← HARD-CODED
    "SUV Compact": {"base_price": 280.0},   # ← HARD-CODED
    "SUV Standard": {"base_price": 350.0},  # ← HARD-CODED
    "SUV Large": {"base_price": 500.0},     # ← HARD-CODED
    "Luxury Sedan": {"base_price": 600.0},  # ← HARD-CODED
    "Luxury SUV": {"base_price": 800.0}     # ← HARD-CODED
}
```

### **What This Means:**
- ✅ **Consistent** - Same base price for all branches (simplified)
- ❌ **Not Data-Driven** - Doesn't reflect actual market prices
- ❌ **Not Dynamic** - Must be manually updated
- ❌ **No Historical Basis** - Not derived from actual contracts

### **Where Base Prices SHOULD Come From:**

**Option A: From Database (Actual Contracts)**
- Source: `Rental.Contract.DailyRateAmount`
- **Data Exists:** 2.48M contracts since 2023
- **Average Price:** 231 SAR/day (median: 190 SAR)
- **Status:** ⚠️ **Available but NOT USED**

**Option B: From Market Research**
- Manual pricing surveys
- Competitor analysis
- **Current Status:** Possibly where hard-coded values came from?

---

## 🔴 **CRITICAL FINDING #2: Historical Price Data Exists BUT Is NOT Used**

### **Database Evidence:**

**Table:** `Rental.Contract`  
**Field:** `DailyRateAmount`  
**Records:** 2,483,704 contracts  
**Date Range:** 2023-01-01 onwards

### **Statistics:**

```
Mean Price:      231 SAR/day
Median Price:    190 SAR/day
Std Deviation:   247 SAR
Min:             9 SAR    (likely error or promo)
25th Percentile: 175 SAR
75th Percentile: 210 SAR
Max:             29,750 SAR (likely monthly rate misclassified)
Missing Values:  9,528 (0.4%)
```

### **Critical Questions:**

1. **Is `DailyRateAmount` the BASE price or FINAL price (after discounts)?**
   - ⚠️ **Unknown** - needs SQL schema investigation
   - Most likely: **FINAL contracted price** (what customer actually paid)
   - May include: Discounts, promotions, negotiated rates, loyalty discounts

2. **Why isn't this used?**
   - Current system uses hard-coded prices
   - No integration between historical prices and base pricing
   - **Recommendation:** Should be used to derive realistic base prices

3. **How do we extract BASE prices from contracted prices?**
   - Need to identify which contracts were at "standard" rates
   - Filter out promotional/discounted contracts
   - Calculate median/mode per category per branch

---

## 🔴 **CRITICAL FINDING #3: Model Predicts DEMAND, Not Prices**

### **What the Model Actually Does:**

**Target Variable:** `DailyBookings` (number of bookings per day per branch)

**Code Evidence** (`robust_model_training_gridsearch.py`, Line 52):
```python
# Create target: daily booking count per branch
demand_counts = df.groupby(['Date', 'PickupBranchId']).size().reset_index(name='DailyBookings')
```

### **What This Means:**

| Model Predicts | Model Does NOT Predict |
|----------------|-------------------------|
| ✅ Number of bookings tomorrow | ❌ Optimal price |
| ✅ Demand level (high/low) | ❌ Price elasticity directly |
| ✅ Utilization forecast | ❌ Revenue maximization |

### **Current Workflow:**

```
1. Model predicts: "Tomorrow you'll have 120 bookings (vs avg 100)"
   ↓
2. Pricing rules say: "120 > 100, so demand is high"
   ↓
3. Apply multiplier: 1.20x (20% premium)
   ↓
4. Final Price: 200 SAR × 1.20 = 240 SAR
```

**The base 200 SAR is STILL hard-coded!**

---

## 🔴 **CRITICAL FINDING #4: Competitor Pricing is 100% SIMULATED**

### **Investigation Results:**

**File:** `live_competitor_pricing.py`

### **NOT Real Scraping:**

```python
# Line 23-56: HARD-CODED base prices
self.base_prices = {
    'Economy': {
        'Hertz': 140,   # ← NOT SCRAPED
        'Budget': 135,  # ← NOT SCRAPED
        'Thrifty': 138  # ← NOT SCRAPED
    },
    # ... (all categories hard-coded)
}
```

### **How It Works (Simulation):**

```python
# Step 1: Start with hard-coded base price
base_price = 140 SAR (Hertz Economy)

# Step 2: Apply location multiplier
if 'airport' in branch_name:
    price *= 1.15  # +15% airport premium

# Step 3: Apply event multiplier
if is_hajj:
    price *= 1.45  # +45% Hajj premium

# Step 4: Add random variation
variation = random(0.97, 1.05)  # -3% to +5%
price *= variation

# Step 5: Round to nearest 5
final_price = round(price / 5) * 5
```

### **Accuracy Assessment:**

| Aspect | Real Scraping | Current System |
|--------|---------------|----------------|
| **Data Source** | Live competitor websites | ❌ Hard-coded estimates |
| **Update Frequency** | Real-time (minutes) | ❌ Never (unless manually updated) |
| **Accuracy** | 95-100% | ⚠️ **Unknown** (no validation) |
| **Event Sensitivity** | Actual market prices | ✅ Simulated (reasonable logic) |
| **Location Sensitivity** | Actual branch prices | ✅ Simulated (reasonable logic) |
| **Random Variation** | N/A | ✅ Simulated (±3-5%) |

### **Critical Questions:**

1. **When were base competitor prices last validated?**
   - ⚠️ **Unknown** - no documentation

2. **How accurate are they?**
   - ⚠️ **Unknown** - no validation against actual competitor sites

3. **Do competitors actually price this way?**
   - ⚠️ **Unknown** - need real market research

---

## 🔴 **CRITICAL FINDING #5: No Connection Between Historical Prices and Base Prices**

### **Data Flow Disconnect:**

```
HISTORICAL DATA (Database)
↓
[Rental.Contract.DailyRateAmount]
↓
Used for: Model training (demand prediction ONLY)
↓
NOT used for: Base pricing
                  ↓
                  ❌ DISCONNECT
                  ↓
DASHBOARD BASE PRICES
↓
[Hard-coded in dashboard_manager.py]
↓
Used for: All pricing recommendations
↓
No connection to actual historical contract prices
```

### **The Problem:**

- Your **base prices** (150, 180, 220 SAR) might not reflect **actual market rates**
- Your **historical contracts** show average of 231 SAR, median 190 SAR
- **Your hard-coded "Economy" = 150 SAR** but **database shows median contract = 190 SAR**
- **Potential revenue loss** if base prices are too low

---

## 📊 **Comparison: Hard-Coded vs Actual Database Prices**

### **Quick Analysis:**

```sql
-- What are actual contract prices by category?
SELECT 
    CategoryName,
    AVG(DailyRateAmount) as AvgPrice,
    MEDIAN(DailyRateAmount) as MedianPrice,
    STDDEV(DailyRateAmount) as StdDev,
    COUNT(*) as ContractCount
FROM Rental.Contract
JOIN Fleet.Vehicles ON ...
JOIN Fleet.Models ON ...
WHERE DailyRateAmount BETWEEN 50 AND 2000  -- Filter outliers
    AND Start >= '2023-01-01'
GROUP BY CategoryName
```

**Recommendation:** Run this query to see if hard-coded prices are realistic!

---

## 🎯 **RECOMMENDATIONS (Priority Order)**

### **🔴 URGENT (Week 1)**

#### **1. Validate Competitor Base Prices**

**Action:** Manual market research
```
Task: Visit 3-5 competitor websites
- Hertz Saudi Arabia
- Budget Saudi Arabia
- Thrifty Saudi Arabia
- Theeb Rent a Car
- Lumi Rental

For each:
- Record prices for Economy, Compact, Standard, SUV
- Check Riyadh Airport vs City prices
- Check for current date vs 1 week out
- Document any promotions/discounts

Compare with hard-coded values in live_competitor_pricing.py
```

**Expected Time:** 2-3 hours  
**Output:** `competitor_price_validation.xlsx`

#### **2. Investigate `DailyRateAmount` Field**

**Action:** SQL Schema Analysis
```sql
-- Check if there are separate fields for base vs final price
SELECT TOP 100
    ContractNumber,
    DailyRateAmount,        -- What is this? Base or final?
    MonthlyRateAmount,
    RentalRateId,          -- Link to rate card?
    -- Are there discount fields?
FROM Rental.Contract
WHERE Start >= '2024-01-01'
ORDER BY CreationTime DESC
```

**Questions to Answer:**
- Is `DailyRateAmount` the base rate or final contracted rate?
- Is there a `RentalRates` table with base pricing?
- Are there discount/promotion fields?
- How do we extract "standard" rates?

**Expected Time:** 1 hour  
**Output:** Understanding of price fields

### **🟡 HIGH PRIORITY (Week 2-3)**

#### **3. Derive Base Prices from Historical Data**

**Action:** Data-Driven Base Pricing

```python
# Example approach:
# 1. Filter contracts to "standard" rates (no promos)
# 2. Group by Category + Branch
# 3. Calculate median price (resistant to outliers)
# 4. Use as new base prices

base_prices = (
    df[df['IsPromotion'] == False]  # If field exists
    .groupby(['Category', 'BranchId'])
    ['DailyRateAmount']
    .median()
)
```

**Expected Time:** 1 week (includes validation)  
**Output:** `data_driven_base_prices.csv`

#### **4. Implement Real Competitor Scraping**

**Options:**

**Option A: Manual Updates (Quick Fix)**
- Weekly manual checks of competitor sites
- Update hard-coded values
- **Time:** 2 hours/week ongoing
- **Accuracy:** 90-95%

**Option B: Actual Web Scraping**
- Use Selenium/BeautifulSoup
- Automate competitor price collection
- **Time:** 2-3 weeks development
- **Accuracy:** 95-99%
- **Challenges:** Site structure changes, CAPTCHAs

**Option C: Third-Party API**
- Use travel aggregator API (e.g., Kayak, Rentalcars.com API)
- **Time:** 1-2 weeks integration
- **Cost:** Subscription required
- **Accuracy:** 99%+

**Recommendation:** Start with Option A (manual), plan for Option C (API)

### **🟢 MEDIUM PRIORITY (Month 2)**

#### **5. Price Elasticity Model (V5 Enhancement)**

**Current:** Model predicts demand (bookings count)  
**Enhancement:** Model predicts demand **as a function of price**

```python
# Instead of:
predict(date, branch, events) → demand

# Do:
predict(date, branch, events, PRICE) → demand
```

**This enables:**
- "If we price at 180 SAR → expect 50 bookings"
- "If we price at 200 SAR → expect 45 bookings"
- "If we price at 220 SAR → expect 38 bookings"
- **Optimal price = maximize revenue (price × bookings)**

**Note:** This was discussed in V5 development but needs actual price variation in historical data.

---

## 📊 **Data Quality Checklist**

### **Immediate Checks Needed:**

```bash
# Run these queries on your database:

# 1. Check price distribution
SELECT 
    MIN(DailyRateAmount) as Min,
    MAX(DailyRateAmount) as Max,
    AVG(DailyRateAmount) as Avg,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DailyRateAmount) as Median,
    COUNT(*) as Total,
    SUM(CASE WHEN DailyRateAmount IS NULL THEN 1 ELSE 0 END) as Nulls,
    SUM(CASE WHEN DailyRateAmount < 50 THEN 1 ELSE 0 END) as TooLow,
    SUM(CASE WHEN DailyRateAmount > 2000 THEN 1 ELSE 0 END) as TooHigh
FROM Rental.Contract
WHERE Start >= '2023-01-01'

# 2. Check if RentalRates table exists (base pricing)
SELECT TOP 10 * 
FROM Rental.RentalRates  -- Does this exist?

# 3. Check for discount/promo fields
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'Rental'
    AND TABLE_NAME = 'Contract'
    AND (
        COLUMN_NAME LIKE '%discount%' OR
        COLUMN_NAME LIKE '%promo%' OR
        COLUMN_NAME LIKE '%base%' OR
        COLUMN_NAME LIKE '%rate%'
    )
```

---

## 🚨 **Business Impact**

### **Current Risks:**

1. **Revenue Risk:**
   - If base prices too low → leaving money on the table
   - If base prices too high → losing bookings to competitors
   - **No data-driven validation**

2. **Competitive Risk:**
   - Competitor prices are simulated, not real
   - May be significantly different from actual market
   - **Could be pricing wrong vs competition**

3. **Decision Risk:**
   - Dashboard shows "8 SAR more than competitors"
   - But competitor price is simulated, not real
   - **Manager decisions based on fake data**

### **Potential Revenue Impact:**

**Scenario:** Base price 10% too low
```
Current: 150 SAR Economy × 1000 bookings/month = 150,000 SAR
Optimal: 165 SAR Economy × 980 bookings/month = 161,700 SAR
Lost Revenue: 11,700 SAR/month per category = ~100,000 SAR/month total
Annual: ~1.2M SAR lost revenue
```

---

## ✅ **Immediate Action Plan**

### **This Week:**

1. **[Day 1-2]** Validate competitor prices manually
   - Check Hertz, Budget, Thrifty websites
   - Document actual prices vs simulated
   - Calculate accuracy percentage

2. **[Day 3]** Investigate database schema
   - Run SQL queries above
   - Document price fields
   - Check for `RentalRates` table

3. **[Day 4-5]** Extract actual base prices from contracts
   - Filter last 6 months
   - Calculate median by category
   - Compare with hard-coded values

4. **[Day 6]** Present findings
   - Current vs should-be prices
   - Competitor accuracy assessment
   - Recommended actions

### **Next Week:**

1. Update hard-coded prices with validated values
2. Implement manual competitor price updates (weekly)
3. Plan for automated scraping or API integration

---

## 📝 **Summary Table**

| Component | Current State | Data Source | Accuracy | Priority |
|-----------|---------------|-------------|----------|----------|
| **Base Prices** | Hard-coded | Unknown/Manual | ⚠️ Unknown | 🔴 URGENT |
| **Historical Prices** | Exists (DailyRateAmount) | Database (2.5M contracts) | ✅ Real data | 🟡 HIGH |
| **Competitor Prices** | Simulated | Hard-coded + multipliers | ⚠️ Unknown | 🔴 URGENT |
| **Demand Model** | Trained (96.57% R²) | Database (bookings count) | ✅ Excellent | ✅ GOOD |
| **Pricing Logic** | Multipliers (working) | Business rules | ✅ Sound logic | ✅ GOOD |

---

## 🎯 **Bottom Line**

### **What's Working:**
- ✅ Demand forecasting model (excellent accuracy)
- ✅ Pricing multiplier logic (sound business rules)
- ✅ System architecture (well-designed)

### **What Needs Fixing:**
- ❌ **Base prices not data-driven** (hard-coded, unknown basis)
- ❌ **Competitor prices not real** (100% simulated)
- ❌ **No validation** of either

### **Next Steps:**
1. **Validate current prices** (1 week)
2. **Update with real data** (2-3 weeks)
3. **Implement ongoing updates** (weekly manual → automated)

---

**Report Generated:** November 30, 2025  
**Classification:** INTERNAL - Management Review Required  
**Action Required:** YES - within 1 week


