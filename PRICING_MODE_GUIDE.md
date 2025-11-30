# Pricing Strategy Mode Guide

## Overview

The Dynamic Pricing Engine supports **two pricing strategies** that you can switch between via the configuration file:

1. **MULTIPLICATIVE (Legacy/Balanced)** - Current approach
2. **HIERARCHICAL (Industry Best Practice)** - Recommended by consultants

---

## 🔄 How to Switch Between Modes

### Configuration File: `config.py`

```python
# Line ~147 in config.py
PRICING_MODE = "hierarchical"  # Options: "multiplicative" or "hierarchical"
```

**To switch:**
1. Open `config.py`
2. Find line `PRICING_MODE = "hierarchical"`
3. Change to either:
   - `"multiplicative"` → Legacy mode
   - `"hierarchical"` → Industry best practice mode
4. Save and restart the dashboard

**No code changes required!** Just change the config value.

---

## 📊 Strategy Comparison

### Strategy 1: MULTIPLICATIVE (Current/Legacy)

#### Philosophy:
All factors are **equally important** and multiply together.

#### Formula:
```
Final Price = Base Price × Demand Multiplier × Supply Multiplier × Event Multiplier
```

#### Example Calculation:
```
Base Price:     200 SAR
Demand:         0.85x (Low demand predicted)
Supply:         1.15x (High utilization - 84%)
Events:         1.00x (No events)

Final = 200 × 0.85 × 1.15 × 1.00
      = 200 × 0.9775
      = 195.50 SAR (-2.3% discount)
```

#### Behavior:
- ✅ **Balanced:** All factors have equal influence
- ✅ **Transparent:** Simple multiplication
- ❌ **Can Cancel Out:** Demand and supply can fight each other (0.85 × 1.15 ≈ 0.98)
- ❌ **No Priority:** Doesn't reflect that demand forecasts are more accurate than supply signals

#### Best For:
- Conservative pricing approach
- When you want all factors to have equal weight
- Testing and comparison purposes

---

### Strategy 2: HIERARCHICAL (Industry Best Practice)

#### Philosophy:
**Demand forecast is PRIMARY**, utilization is **SECONDARY** (guardrail/accelerator).

Follows revenue management standards used by:
- ✈️ **Emirates Airlines**
- 🏨 **Booking.com**
- 🚗 **Hertz, Enterprise**

#### Formula:
```
1. Primary Signal = Demand × Events (sets direction)
2. Utilization Role = Depends on scenario:
   - If discount predicted → Constrains how low we go
   - If premium predicted → Accelerates how high we go
   - If neutral → Utilization drives
```

#### Example 1: Low Demand + High Utilization
```
Base Price:         200 SAR
Demand:             0.85x (15% below average)
Events:             1.00x (No events)
Utilization:        84% (HIGH)

Step 1: Primary Signal = 0.85 × 1.00 = 0.85 (-15% discount)
Step 2: High Utilization → CONSTRAINS discount (apply only 40%)
        Adjustment = 1 + (0.85 - 1) × 0.40
                   = 1 + (-0.15 × 0.40)
                   = 0.94

Final = 200 × 0.94 = 188 SAR (-6% discount)

Logic: "Demand says -15%, but we're 84% full, so only apply -6%"
```

#### Example 2: High Demand + High Utilization
```
Base Price:         200 SAR
Demand:             1.20x (20% above average)
Events:             1.00x (No events)
Utilization:        84% (HIGH)

Step 1: Primary Signal = 1.20 × 1.00 = 1.20 (+20% premium)
Step 2: High Utilization → ACCELERATES premium (amplify by 30%)
        Adjustment = 1 + (1.20 - 1) × 1.30
                   = 1 + (0.20 × 1.30)
                   = 1.26

Final = 200 × 1.26 = 252 SAR (+26% premium)

Logic: "Demand says +20%, and we're 84% full, so push to +26%"
```

#### Example 3: Neutral Demand + High Utilization
```
Base Price:         200 SAR
Demand:             1.00x (Average demand)
Events:             1.00x (No events)
Utilization:        84% (HIGH)

Step 1: Primary Signal = 1.00 (neutral)
Step 2: Neutral demand → Let utilization drive
        Adjustment = Supply Multiplier = 1.15

Final = 200 × 1.15 = 230 SAR (+15% premium)

Logic: "No demand signal, so utilization takes over"
```

#### Behavior:
- ✅ **Demand-Driven:** Prioritizes the most accurate predictor (AI model with 96.57% R²)
- ✅ **Contextual Utilization:** Uses utilization intelligently based on scenario
- ✅ **Industry Standard:** Aligns with Emirates/Booking.com practices
- ✅ **Business Logic:** Follows consultant recommendations
- ✅ **No Cancellation:** Demand and supply work together, not against each other

#### Best For:
- **Recommended for production use**
- Aligning with industry best practices
- Maximizing revenue management effectiveness
- Following consultant recommendations

---

## ⚙️ Fine-Tuning Hierarchical Mode

### Adjustable Parameters in `config.py`:

```python
HIERARCHICAL_CONFIG = {
    # Discount constraints (when demand is LOW)
    'discount_constraint_high_util': 0.40,    # >80% utilized: Apply 40% of discount
    'discount_constraint_medium_util': 0.70,  # 60-80%: Apply 70% of discount
    'discount_constraint_low_util': 1.00,     # <60%: Apply 100% of discount
    
    # Premium acceleration (when demand is HIGH)
    'premium_acceleration_high_util': 1.30,   # >80% utilized: Amplify premium by 30%
    'premium_acceleration_medium_util': 1.15, # 60-80%: Amplify premium by 15%
    'premium_acceleration_low_util': 1.00,    # <60%: Standard premium
    
    # Utilization thresholds
    'high_utilization_threshold': 80,    # Above this = "high"
    'medium_utilization_threshold': 60,  # Between this and high = "medium"
}
```

### What Each Parameter Does:

#### Discount Constraints:
**Higher values = MORE aggressive discounts when busy**

- `discount_constraint_high_util = 0.40`:
  - When 84% utilized and demand says -15% discount
  - Only apply 40% of the discount = -6% final discount
  - **Increase to 0.60** → Would apply -9% discount (more aggressive)
  - **Decrease to 0.20** → Would apply -3% discount (more conservative)

#### Premium Acceleration:
**Higher values = MORE aggressive premiums when busy**

- `premium_acceleration_high_util = 1.30`:
  - When 84% utilized and demand says +20% premium
  - Amplify to +26% premium (20% × 1.30)
  - **Increase to 1.50** → Would apply +30% premium (more aggressive)
  - **Decrease to 1.10** → Would apply +22% premium (more conservative)

#### Utilization Thresholds:
- `high_utilization_threshold = 80`: Above 80% = "high utilization"
- `medium_utilization_threshold = 60`: 60-80% = "medium utilization"

**Adjust these to change when constraints/accelerations kick in.**

---

## 🧪 Testing & Comparison

### Recommended Approach:

1. **Week 1: Run Multiplicative Mode**
   - Set `PRICING_MODE = "multiplicative"`
   - Track revenue, bookings, utilization
   - Export results

2. **Week 2: Run Hierarchical Mode**
   - Set `PRICING_MODE = "hierarchical"`
   - Track same metrics
   - Export results

3. **Compare:**
   - Revenue per vehicle
   - Booking conversion rate
   - Average utilization
   - Price competitiveness

4. **Choose Winner:**
   - Select the mode that performs best
   - Fine-tune parameters if needed

### Real-Time Comparison:

You can also switch modes during the day:
- **Morning:** Use multiplicative
- **Afternoon:** Switch to hierarchical
- **Compare:** Same-day metrics

---

## 📱 Dashboard Integration

### Mode Indicator:
The dashboard automatically shows which mode is active:

**Hierarchical Mode:**
```
✅ Pricing Strategy: HIERARCHICAL (Industry Best Practice)

Following Emirates/Booking.com/Hertz standards:
- 🎯 Demand forecast = PRIMARY driver
- 🚗 Fleet utilization = SECONDARY (guardrail/accelerator)
```

**Multiplicative Mode:**
```
ℹ️ Pricing Strategy: MULTIPLICATIVE (Legacy/Balanced)

All factors are weighted equally:
- Demand × Supply × Events = Final Price
```

### Pricing Cards:
Each category card shows:
- Individual multipliers (Demand, Supply, Events)
- **Mode Explanation** (hierarchical only):
  - "Demand-led discount (-15%), constrained by high utilization to -6%"
  - "Demand-led premium (+20%), accelerated by high utilization to +26%"

---

## 🎯 Consultant Recommendations

Based on your consultant's feedback:

### ✅ What You're Doing Right:
1. ✅ Excellent demand forecasting (V4 model, 96.57% R²)
2. ✅ Real-time utilization tracking
3. ✅ Price elasticity modeling (V5)
4. ✅ Event awareness (Ramadan, Hajj, holidays)
5. ✅ Competitor intelligence

### 🔧 What Hierarchical Mode Fixes:
1. ✅ **Demand as PRIMARY driver** (not equal weight)
2. ✅ **Utilization as SECONDARY** (guardrail/accelerator, not co-equal)
3. ✅ **Industry alignment** (Emirates, Booking.com, Hertz)
4. ✅ **No more cancellation** (demand and supply work together)

### 📊 Alignment Score:

| Aspect | Multiplicative | Hierarchical |
|--------|----------------|--------------|
| Demand Forecasting | ✅ Yes | ✅ Yes |
| Utilization Tracking | ✅ Yes | ✅ Yes |
| **Demand Priority** | ❌ Equal weight | ✅ Primary |
| **Utilization Role** | ❌ Co-equal | ✅ Guardrail |
| **Industry Standard** | ❌ No | ✅ Yes |

---

## 🚀 Quick Start

### To Use Hierarchical Mode (Recommended):

1. Open `config.py`
2. Set:
   ```python
   PRICING_MODE = "hierarchical"
   ```
3. Save and restart dashboard:
   ```bash
   streamlit run dashboard_manager.py --server.port 8502
   ```

### To Revert to Multiplicative Mode:

1. Open `config.py`
2. Set:
   ```python
   PRICING_MODE = "multiplicative"
   ```
3. Save and restart dashboard

---

## 📞 Support

**Questions? Issues? Want to discuss strategy?**

The system is flexible - you control the strategy via config.

**No code changes needed.** Just change `PRICING_MODE` in `config.py` and restart!

---

## 📝 Summary

| Feature | Multiplicative | Hierarchical |
|---------|----------------|--------------|
| **Demand Role** | Equal (33%) | Primary (100%) |
| **Utilization Role** | Equal (33%) | Secondary (guardrail) |
| **Events Role** | Equal (33%) | Stacks with demand |
| **Can Cancel Out** | ✅ Yes | ❌ No |
| **Industry Standard** | ❌ No | ✅ Yes |
| **Consultant-Approved** | ❌ No | ✅ Yes |
| **Configuration** | `PRICING_MODE = "multiplicative"` | `PRICING_MODE = "hierarchical"` |

**Recommendation:** Use `"hierarchical"` for production, aligns with best practices. ✅


