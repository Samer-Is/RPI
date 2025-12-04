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

Deploy a **production** internal web-based dashboard for dynamic pricing recommendations. The application will:
- Connect to the **Renty Production SQL Server database** (read-only)
- Display real-time pricing recommendations to branch managers
- Fetch competitor pricing data from external API
- Run 24/7 for business operations

---

## Server Requirements

### Option A: Windows Server (Recommended)

| Specification | Minimum | Recommended |
|---------------|---------|-------------|
| **OS** | Windows Server 2019+ | Windows Server 2022 |
| **CPU** | 2 vCPU | 4 vCPU |
| **RAM** | 4 GB | 8 GB |
| **Storage** | 50 GB SSD | 100 GB SSD |
| **Network** | Internal + Internet | Internal + Internet |

### Option B: Linux Server

| Specification | Minimum | Recommended |
|---------------|---------|-------------|
| **OS** | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| **CPU** | 2 vCPU | 4 vCPU |
| **RAM** | 4 GB | 8 GB |
| **Storage** | 50 GB SSD | 100 GB SSD |
| **Network** | Internal + Internet | Internal + Internet |

---

## Network Requirements

### Inbound Access (Required)
| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 8501 | TCP | Internal Network | Dashboard web access |
| 22 | TCP | IT Admin IPs only | SSH (Linux) / RDP (Windows) |

### Outbound Access (Required)
| Destination | Port | Purpose |
|-------------|------|---------|
| **Renty Production SQL Server** | 1433 | Database queries (read-only) |
| rapidapi.com | 443 (HTTPS) | Competitor pricing API |
| pypi.org | 443 (HTTPS) | Python package installation (one-time setup) |

---

## Production Requirements

### High Availability
- [ ] Auto-restart on server reboot
- [ ] Service monitoring (optional)
- [ ] Daily backup of application files

### Security
- [ ] Firewall rules as specified above
- [ ] Database service account with minimal permissions
- [ ] HTTPS/SSL certificate (optional, for secure access)

---

## Database Access Required (PRODUCTION)

**Connection Type:** Read-only access to **Renty Production SQL Server**

**Server:** [Production SQL Server Name/IP]  
**Database:** [Production Database Name]  
**Port:** 1433  

**Tables Needed (SELECT Only):**
| Schema | Table | Purpose |
|--------|-------|---------|
| `Fleet` | `VehicleHistory` | Real-time vehicle utilization |
| `Fleet` | `Vehicles` | Vehicle master data |
| `Fleet` | `Models` | Vehicle categories |
| `Rental` | `Contract` | Rental history & pricing |
| `Rental` | `Branches` | Branch information |
| `Rental` | `Cities` | City reference |

**Service Account Request:**
- Create a dedicated **production service account** for the application
- Account name suggestion: `svc_dynamic_pricing`
- Grant **SELECT permissions only** (no INSERT/UPDATE/DELETE)
- Restrict access to tables listed above
- Enable Windows Authentication or SQL Authentication

---

## Software to be Installed

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Application runtime |
| pip | Latest | Package manager |
| ODBC Driver | SQL Server 17+ | Database connectivity |
| Git | Latest | Code deployment |

**Python Packages (installed via pip):**
```
streamlit==1.28.0
pandas==2.1.0
numpy==1.24.0
xgboost==2.0.0
scikit-learn==1.3.0
pyodbc==5.0.0
plotly==5.18.0
requests==2.31.0
```

---

## Access Requirements

### Users Who Need Dashboard Access
- Branch Managers (view pricing recommendations)
- Pricing Team (view and analyze)
- [Add specific users/groups]

### Admin Access
- [Your Name] — Application deployment and maintenance
- IT Support — Server administration

---

## Deployment Plan

1. **Server provisioning** — IT creates VM with specifications above
2. **Network configuration** — Open required ports
3. **Database access** — DBA creates read-only service account
4. **Software installation** — Install Python and dependencies
5. **Application deployment** — Deploy code and configure
6. **Testing** — Verify connectivity and functionality
7. **Go-live** — Share dashboard URL with users

---

## Dashboard URL (After Deployment)

```
http://[SERVER-IP]:8501
```

Or with custom DNS:
```
http://pricing.renty.local:8501
```

---

## Support & Maintenance

| Activity | Frequency | Responsible |
|----------|-----------|-------------|
| Server patching | Monthly | IT |
| Application updates | As needed | [Your Name] |
| Database access review | Quarterly | DBA |
| Backup | Daily (server) | IT |

---

## Contact for Questions

**Technical Contact:** [Your Name]  
**Email:** [Your Email]  
**Phone:** [Your Phone]  

---

## Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Requestor | | | |
| Manager | | | |
| IT Approval | | | |
| DBA Approval | | | |

---

*Please contact me if you need any additional technical details or clarification.*

