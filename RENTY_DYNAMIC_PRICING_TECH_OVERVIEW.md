# RENTY Dynamic Pricing
## Technical Overview

---

# SLIDE 1: System Architecture

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│     📊 DATA SOURCES              🧠 AI ENGINE                   │
│     ───────────────              ──────────────                 │
│                                                                  │
│     ┌─────────────┐             ┌─────────────┐                 │
│     │   Renty     │────────────►│  Demand     │                 │
│     │  Database   │             │  Forecast   │                 │
│     │ (Real-time) │             │(High Accuracy)                │
│     └─────────────┘             └──────┬──────┘                 │
│                                        │                         │
│     ┌─────────────┐             ┌──────▼──────┐                 │
│     │ Competitor  │────────────►│  Pricing    │                 │
│     │   Prices    │             │   Rules     │                 │
│     │   (API)     │             │  Engine     │                 │
│     └─────────────┘             └──────┬──────┘                 │
│                                        │                         │
│     ┌─────────────┐             ┌──────▼──────┐                 │
│     │   Saudi     │────────────►│  Optimized  │                 │
│     │  Calendar   │             │   Price     │                 │
│     │  (Events)   │             │             │                 │
│     └─────────────┘             └─────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

| Component | Function |
|-----------|----------|
| **Fleet Utilization** | Real-time vehicle availability per branch |
| **Demand Forecasting** | AI-powered prediction with high accuracy |
| **Competitor Intelligence** | Daily pricing from major rental companies |
| **Event Calendar** | Ramadan, Hajj, holidays, school vacations |
| **Pricing Rules** | Business logic for premiums and discounts |

---

# SLIDE 2: Technology Stack

## Platform Technologies

| Layer | Technology | Purpose |
|-------|------------|---------|
| **AI/ML** | Python + Machine Learning | Demand forecasting |
| **Database** | SQL Server | Fleet & rental data |
| **API** | Booking.com (RapidAPI) | Competitor prices |
| **Dashboard** | Streamlit | Interactive UI |
| **Visualization** | Plotly | Charts & analytics |

## Data Integration

| Source | Data | Update Frequency |
|--------|------|------------------|
| Fleet.VehicleHistory | Utilization | Real-time |
| Rental.Contract | Pricing history | Real-time |
| Competitor API | Market prices | Daily |
| Saudi Calendar | Events & holidays | Monthly |

## Key Capabilities

✅ **8 Vehicle Categories** — Economy to Luxury SUV  
✅ **5+ Active Branches** — Airports and city locations  
✅ **6+ Competitors Tracked** — Alamo, Enterprise, Sixt, Budget, Hertz  
✅ **Dynamic Multipliers** — Demand, supply, and event-based pricing  
✅ **Real-time Dashboard** — Branch manager pricing tool  

---

**RENTY Dynamic Pricing** — AI-Powered Revenue Optimization

