# Server/VM Request for RENTY Dynamic Pricing Tool

## Request Summary

**Project:** RENTY Dynamic Pricing Dashboard  
**Environment:** 🔴 **PRODUCTION**  
**Requested By:** [Your Name]  
**Department:** [Your Department]  
**Date:** [Date]  
**Priority:** High  

---

## Purpose

Deploy a **production** internal web-based dashboard for dynamic pricing recommendations.

**Note:** This is a **standalone application** - NO database connection required. All data is stored locally on the server.

---

## Server Requirements

### Recommended Specs

| Specification | Requirement |
|---------------|-------------|
| **OS** | Windows Server 2022 or Ubuntu 22.04 LTS |
| **CPU** | 4 vCPU |
| **RAM** | 8 GB |
| **Storage** | 100 GB SSD |

---

## Network Requirements

### Inbound Access
| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 8501 | TCP | Internal Network | Dashboard web access |
| 3389/22 | TCP | IT Admin IPs only | RDP (Windows) / SSH (Linux) |

### Outbound Access
| Destination | Port | Purpose |
|-------------|------|---------|
| rapidapi.com | 443 (HTTPS) | Competitor pricing API |
| pypi.org | 443 (HTTPS) | Python packages (one-time setup) |

**⚠️ NO SQL Server connection required**

---

## Software to be Installed

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Application runtime |
| pip | Latest | Package manager |
| Git | Latest | Code deployment |

---

## Data Storage (Local Files)

All data will be stored locally on the server:

| File | Purpose | Update Method |
|------|---------|---------------|
| `vehicle_history.csv` | Fleet utilization data | Manual upload / scheduled export |
| `competitor_prices.json` | Competitor pricing | Auto-updated via API |
| `demand_model.pkl` | ML model | Pre-trained, static |

**No live database connection needed.**

---

## Access Requirements

### Dashboard Users
- Branch Managers (internal network access to port 8501)

### Admin Access
- [Your Name] — Application deployment and maintenance
- IT Support — Server administration

---

## Dashboard URL (After Deployment)

```
http://[SERVER-IP]:8501
```

---

## Simple Email Version

> **Subject:** VM Request - RENTY Dynamic Pricing Dashboard
>
> Hi Team,
>
> I need a VM for an internal web dashboard:
>
> **Server:** 4 vCPU, 8GB RAM, 100GB SSD, Windows Server 2022  
> **Network:** Port 8501 open internally, outbound internet (HTTPS only)  
> **Software:** Python 3.11  
>
> **No database connection required** - all data stored locally.
>
> Thanks!

---

**Contact:** [Your Name] - [Your Email]
