# Quick Start: Pricing Modes

## 🎯 **Your Question Answered**

**Q: "High utilization yet discount?"**

**A: This happens in MULTIPLICATIVE mode when:**
- **Demand** predicts discount (-15%): `0.85x`
- **Supply** predicts premium (+15%): `1.15x`
- They **multiply together**: `0.85 × 1.15 = 0.9775` → **-2.3% discount**
- Result: **They cancel each other out!**

---

## ✅ **Solution: HIERARCHICAL Mode**

Your consultants are RIGHT:
- **Demand should be PRIMARY** (it's your 96.57% accurate AI model)
- **Utilization should be SECONDARY** (guardrail/accelerator)

Same scenario in HIERARCHICAL mode:
- Demand says: **-15% discount**
- Utilization says: **"But we're 84% full, so limit to -6%"**
- Result: **-6% discount** (demand leads, utilization constrains)

---

## 🔧 **How to Switch (One Line Change)**

### Open: `config.py` (Line ~147)

```python
# For MULTIPLICATIVE (Current/Legacy - factors cancel out):
PRICING_MODE = "multiplicative"

# For HIERARCHICAL (Best Practice - demand leads):
PRICING_MODE = "hierarchical"  # ← RECOMMENDED
```

**Save and restart dashboard. Done!**

---

## 📊 **Real Example (Your Current Situation)**

### Inputs:
- Utilization: **84%** (High)
- Demand Forecast: **15% below average**
- Base Price: **200 SAR**

### MULTIPLICATIVE Result:
```
0.85 (demand) × 1.15 (supply) × 1.00 (events) = 0.9775
Final: 195.5 SAR (-2.3% discount)
Logic: "Factors fight each other, minimal impact"
```

### HIERARCHICAL Result:
```
Demand = PRIMARY (-15% discount)
Supply = SECONDARY (constrains to 40% of discount)
Final adjustment: 1 + (0.85 - 1) × 0.40 = 0.94
Final: 188 SAR (-6% discount)
Logic: "Demand says discount, but utilization limits how low we go"
```

**Difference:** 7.5 SAR (3.7 percentage points)

---

## 🎓 **Which Mode to Use?**

### Use MULTIPLICATIVE if:
- ❓ You want all factors equally weighted
- ❓ You're comfortable with factors canceling out
- ✅ You're testing/comparing

### Use HIERARCHICAL if: ✅ **RECOMMENDED**
- ✅ You want to follow Emirates/Booking.com/Hertz
- ✅ You trust your demand AI model (96.57% R²)
- ✅ You want consultant-approved approach
- ✅ You want demand to LEAD, utilization to MODULATE

---

## 🚀 **Quick Actions**

### 1. See Comparison:
```bash
python compare_pricing_modes.py
```
→ Shows side-by-side results for 5 scenarios

### 2. Read Full Guide:
→ Open `PRICING_MODE_GUIDE.md`

### 3. Switch to Hierarchical (Recommended):
```python
# In config.py:
PRICING_MODE = "hierarchical"
```
→ Restart dashboard

### 4. Fine-Tune (Optional):
```python
# In config.py, adjust these:
HIERARCHICAL_CONFIG = {
    'discount_constraint_high_util': 0.40,   # Higher = more aggressive discounts
    'premium_acceleration_high_util': 1.30,  # Higher = more aggressive premiums
    # ... see PRICING_MODE_GUIDE.md for details
}
```

---

## 📞 **Summary**

| Question | Answer |
|----------|--------|
| **Why discount at 84% utilization?** | In multiplicative mode, demand (0.85) × supply (1.15) = 0.98 |
| **Is this correct?** | Technically yes, but not optimal per consultants |
| **What should I do?** | Switch to `PRICING_MODE = "hierarchical"` in config.py |
| **What will change?** | Demand will LEAD, utilization will CONSTRAIN/ACCELERATE |
| **Is it reversible?** | Yes! Just change config back to "multiplicative" |
| **Do I need code changes?** | NO! Just config change and restart |

---

## ✅ **Consultant Approval**

Your consultants said:
> "Demand forecast first, utilization second as a guardrail."

**Hierarchical mode implements EXACTLY this!** ✅

---

**Ready to switch?**
1. Open `config.py`
2. Set `PRICING_MODE = "hierarchical"`
3. Save and restart dashboard
4. Done! 🎉


