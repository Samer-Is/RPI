# 🔍 Competitor Price Validation Guide

## Purpose
Manually validate the accuracy of simulated competitor prices against actual market prices.

**Time Required:** 2-3 hours  
**Frequency:** Weekly (until automated scraping is implemented)  
**Output:** `competitor_price_validation_results.xlsx`

---

## 📋 Preparation

### **Tools Needed:**
- Web browser (Chrome/Firefox recommended)
- Excel/Google Sheets for recording
- VPN (optional, to avoid rate limiting)
- Template spreadsheet (see below)

### **Competitors to Check:**
1. **Hertz Saudi Arabia** - https://www.hertz.com.sa/
2. **Budget Saudi Arabia** - https://www.budget.com.sa/
3. **Thrifty Saudi Arabia** - https://www.thrifty.com.sa/
4. **Theeb Rent a Car** - https://www.theeb.com.sa/
5. **Lumi Rental** - https://www.lumirentacar.com/

---

## 📊 Validation Template

Create a spreadsheet with these columns:

| Date | Competitor | Location | Category | Pickup Date | Duration | Website Price | Simulated Price | Difference | % Diff | Notes |
|------|------------|----------|----------|-------------|----------|---------------|-----------------|------------|--------|-------|
| 2025-11-30 | Hertz | Riyadh Airport | Economy | 2025-12-07 | 1 day | 145 SAR | 140 SAR | +5 SAR | +3.4% | Weekend |

---

## 🔍 Validation Procedure

### **Step 1: Set Test Parameters**

**Test Scenarios:**
1. **Riyadh Airport** - Economy, 7 days out, 1-day rental, weekday
2. **Riyadh Airport** - SUV Standard, 7 days out, 1-day rental, weekend
3. **Jeddah Airport** - Compact, 7 days out, 1-day rental, weekday
4. **Riyadh City** - Standard, 7 days out, 1-day rental, weekday
5. **Mecca** - Economy, 7 days out, 1-day rental, (if available)

**Why these scenarios?**
- Airport vs City (tests location multiplier)
- Weekend vs Weekday (tests day multiplier)
- Different categories (tests category pricing)
- 7 days out (avoids last-minute premiums)

---

### **Step 2: Check Each Competitor**

For **each competitor**, follow this process:

#### **A. Visit Website**

```
1. Go to competitor website
2. Select:
   - Pickup: [Test Location] (e.g., "King Khalid International Airport, Riyadh")
   - Pickup Date: [7 days from today]
   - Pickup Time: 10:00 AM
   - Return Date: [Next day]
   - Return Time: 10:00 AM
3. Click "Search" or "Find Cars"
```

#### **B. Record Prices**

```
4. Find the test category (e.g., "Economy" or equivalent)
5. Record the DAILY RATE (not total price)
   - Look for "SAR/day" or "Per Day"
   - If only total shown: Total ÷ Days = Daily Rate
6. Note any:
   - Discounts/Promotions active
   - Insurance included/excluded
   - Mileage limits
   - Special conditions
```

#### **C. Get Simulated Price for Comparison**

```python
# Run this in Python to get simulated price:
from live_competitor_pricing import LiveCompetitorPricing
from datetime import datetime, timedelta

scraper = LiveCompetitorPricing()

# Adjust parameters to match your test:
result = scraper.get_live_prices(
    category="Economy",              # Match your test
    branch_name="Riyadh Airport",    # Match your test
    date=datetime.now() + timedelta(days=7),  # 7 days out
    is_weekend=False,                # Adjust
    is_holiday=False
)

# Get specific competitor price
hertz_price = next((c['Competitor_Price'] for c in result['competitors'] 
                   if c['Competitor_Name'] == 'Hertz'), None)

print(f"Simulated Hertz Price: {hertz_price} SAR")
```

---

### **Step 3: Calculate Accuracy**

For each comparison:

```
Difference = Actual Website Price - Simulated Price
% Difference = (Difference / Actual Website Price) × 100
```

**Accuracy Thresholds:**
- ✅ **Excellent:** ±5% or less
- ⚠️ **Acceptable:** ±5-10%
- ❌ **Poor:** >±10%

---

## 📋 Validation Checklist

### **Quick Check (30 minutes):**

- [ ] Hertz - Riyadh Airport - Economy - Weekday
- [ ] Budget - Riyadh Airport - Economy - Weekday
- [ ] Thrifty - Riyadh Airport - Economy - Weekday
- [ ] Compare with simulated prices
- [ ] Calculate average % difference

**If average difference > 10%:** Do full validation

---

### **Full Validation (2-3 hours):**

**Category Coverage:**
- [ ] Economy (3 competitors × 2 locations)
- [ ] Compact (3 competitors × 2 locations)
- [ ] Standard (3 competitors × 2 locations)
- [ ] SUV Standard (3 competitors × 2 locations)
- [ ] SUV Large (2 competitors × 1 location)
- [ ] Luxury Sedan (2 competitors × 1 location)

**Location Coverage:**
- [ ] Riyadh Airport
- [ ] Jeddah Airport
- [ ] Riyadh City Center
- [ ] Mecca (if available)

**Day Coverage:**
- [ ] Weekday (Tuesday/Wednesday)
- [ ] Weekend (Thursday/Friday)

**Total Checks:** ~30-40 price points

---

## 🔧 Common Issues & Solutions

### **Issue 1: Category Naming Mismatch**

**Problem:** Competitor calls it "Compact SUV" but you search "SUV Compact"

**Solution:** Create mapping table:

| Renty Category | Hertz | Budget | Thrifty | Theeb | Lumi |
|----------------|-------|--------|---------|-------|------|
| Economy | Economy | Economy | Economy | Economy | Economy |
| Compact | Compact | Compact | Compact | Compact | Compact |
| Standard | Standard | Midsize | Standard | Standard | Standard |
| SUV Compact | Compact SUV | Small SUV | Compact SUV | SUV | Compact SUV |

### **Issue 2: Prices Include Insurance**

**Problem:** Competitor price includes insurance, yours doesn't

**Solution:** 
- Try to find "Base Rate" or "Car Only" price
- If not available, note in "Notes" column
- Subtract typical insurance (usually 20-30 SAR/day)

### **Issue 3: Competitor Site Requires Login**

**Problem:** Can't see prices without account

**Solution:**
- Create free account
- Or call customer service and ask for quote
- Or skip and note "Unable to verify"

### **Issue 4: No Cars Available**

**Problem:** "Sorry, no vehicles available"

**Solution:**
- Try different date (±1-2 days)
- Try different location
- Note in spreadsheet as "Not Available"

---

## 📊 Analysis Template

After collecting data, calculate:

### **1. Overall Accuracy**

```
Average Absolute % Difference = Σ(|% Diff|) / N

Example:
Hertz Economy: +5%
Hertz SUV: -3%
Budget Economy: +8%
Budget SUV: -2%

Average = (5 + 3 + 8 + 2) / 4 = 4.5%

✅ <5% = Excellent
⚠️ 5-10% = Acceptable
❌ >10% = Needs Update
```

### **2. Bias Check**

```
Average % Difference (signed) = Σ(% Diff) / N

Example:
+5%, -3%, +8%, -2% → Average = +2%

Positive = Simulated prices are LOWER than actual (losing revenue!)
Negative = Simulated prices are HIGHER than actual (losing bookings!)
```

### **3. Worst Cases**

Identify:
- Largest positive difference (most underpriced)
- Largest negative difference (most overpriced)
- Most inconsistent competitor
- Most inconsistent category

---

## 📝 Sample Results Summary

```
VALIDATION SUMMARY
Date: November 30, 2025
Validator: [Your Name]
Total Checks: 32

OVERALL ACCURACY:
- Average Absolute Difference: 8.2%
- Average Signed Difference: +3.1% (simulated LOWER)
- Range: -12% to +18%

BY COMPETITOR:
- Hertz:   Avg 6.5% (Acceptable)
- Budget:  Avg 9.2% (Borderline)
- Thrifty: Avg 11.8% (Needs Update)

BY CATEGORY:
- Economy:      Avg 5.1% ✅
- Compact:      Avg 7.3% ⚠️
- Standard:     Avg 8.9% ⚠️
- SUV Standard: Avg 12.4% ❌ NEEDS UPDATE

BY LOCATION:
- Riyadh Airport: Avg 7.8%
- Jeddah Airport: Avg 9.1%
- Riyadh City:    Avg 6.2%

CRITICAL FINDINGS:
1. SUV categories are underpriced by ~10-15%
2. Thrifty prices have changed significantly (all categories)
3. Weekend multiplier seems accurate (within 3%)
4. Airport multiplier too high for Jeddah (+18% vs actual +10%)

RECOMMENDED ACTIONS:
1. Update SUV base prices:
   - SUV Standard: 350 → 380 SAR (+8.6%)
   - SUV Large: 500 → 550 SAR (+10%)
2. Revise Thrifty base prices across all categories
3. Reduce Jeddah airport multiplier from 1.15 to 1.10
```

---

## 🔄 Update Process

Once validation is complete:

### **Step 1: Update Simulated Base Prices**

Edit `live_competitor_pricing.py`:

```python
# OLD:
'SUV Standard': {
    'Hertz': 340,
    'Budget': 335,
    'Thrifty': 345
}

# NEW (after validation):
'SUV Standard': {
    'Hertz': 370,  # +8.8% adjustment
    'Budget': 365,  # +9.0% adjustment
    'Thrifty': 375  # +8.7% adjustment
}
```

### **Step 2: Update Multipliers (if needed)**

```python
# OLD:
self.location_multipliers = {
    'airport': 1.15,
    'city': 1.0,
    'mecca': 1.25,
}

# NEW (if validation shows different):
self.location_multipliers = {
    'airport': 1.12,  # Adjusted based on validation
    'city': 1.0,
    'mecca': 1.20,    # Adjusted
}
```

### **Step 3: Document Changes**

Create entry in `COMPETITOR_PRICE_UPDATE_LOG.md`:

```markdown
## Update 2025-11-30

### Changes Made:
- Increased SUV Standard base prices by ~9% across all competitors
- Reduced airport multiplier from 1.15 to 1.12
- Updated Thrifty base prices for all categories

### Validation Results:
- Previous accuracy: 8.2% average difference
- New estimated accuracy: ~5% (to be validated next week)

### Data Source:
- Manual validation of 32 price points
- Competitors checked: Hertz, Budget, Thrifty
- Locations: Riyadh Airport, Jeddah Airport, Riyadh City
```

### **Step 4: Re-run Validation (1 week later)**

- Check if accuracy improved
- Target: <5% average difference
- If still >8%, repeat update process

---

## 📅 Ongoing Schedule

**Weekly (until automated):**
- Quick check (30 min): 5-10 price points
- Update if >10% difference

**Monthly:**
- Full validation (2-3 hours): 30-40 price points
- Comprehensive update
- Document changes

**Quarterly:**
- Deep dive: All categories, all locations
- Review multiplier logic
- Consider seasonal adjustments

---

## ✅ Success Criteria

**Target Accuracy:**
- Overall: <5% average absolute difference
- Per competitor: <7%
- Per category: <8%
- No single price: >15% difference

**When Achieved:**
- Simulated prices are reliable for business decisions
- Dashboard competitor comparisons are trustworthy
- Can proceed with confidence until automated scraping

---

## 🚀 Next Steps After Validation

1. **Short-term:** Weekly manual updates
2. **Medium-term:** Build automated scraper (2-3 weeks)
3. **Long-term:** Use API service (e.g., Kayak/Rentalcars.com)

---

**Last Updated:** November 30, 2025  
**Next Validation Due:** December 7, 2025  
**Validator:** [Assign Name]


