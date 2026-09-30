# Zabbix Operations UI - Architecture Specification

## 1. System Overview
**Zabbix Operations UI** is an enterprise-grade operational interface and observability layer built for an existing **Zabbix 7.0.5** infrastructure.

### Architectural Flow:
```text
Browser (React Frontend)
       ↓  HTTP / REST
FastAPI Backend API (/ops-api)
       ↓  Normalized DTOs
Zabbix Adapter Layer (RealZabbixAdapter | MockZabbixAdapter)
       ↓  JSON-RPC 2.0
Zabbix 7.0.5 Server
```

---

## 2. Key Design Principles

1. **Non-Invasive Architecture:**
   - Zabbix core files, frontend PHP, and database schemas remain 100% untouched.
   - All monitoring telemetry (Hosts, Items, Triggers, Events, History, Trends, SLAs) is queried via Zabbix API.
2. **Offline-First Production Deployment:**
   - Target production Linux server has **NO INTERNET ACCESS**.
   - Build artifacts (React `dist/`, Python wheel dependencies, systemd unit, Apache proxy configs) are pre-packaged on the connected developer machine and transferred manually.
3. **Zabbix Adapter Isolation:**
   - The application accesses Zabbix only through the `ZabbixAdapterBase` interface.
   - `MockZabbixAdapter`: Used in local development when offline from the production network.
   - `RealZabbixAdapter`: Used in production with the official Zabbix 7.0.5 JSON-RPC endpoint.
   - Mock data is strictly prevented from executing in production (`APP_ENV=production` & `ZABBIX_ADAPTER_TYPE=real`).
4. **Data Integrity & Truth:**
   - Missing data is reported as `N/A`, never as `0` or `100%`.
   - Availability is calculated from actual measured time intervals, not averaged arbitrary item states.

---

## 3. Technology Stack

### Frontend
- **Framework:** React 19 + TypeScript
- **Bundler:** Vite
- **UI Components:** Material UI (MUI) / Vanilla CSS (Dark mode enterprise NOC aesthetic)
- **Tables:** TanStack Table
- **Charts:** Apache ECharts
- **Routing:** React Router

### Backend
- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Data Validation:** Pydantic v2
- **HTTP Client:** HTTPX (async JSON-RPC)
- **ORM / Migrations:** SQLAlchemy 2.0 & Alembic (for application-specific metadata/saved views)

### Production Deployment Target
- **Web Server:** Existing Apache HTTP Server (`/ops` for frontend, `/ops-api` for backend proxy)
- **Process Manager:** Systemd (`zabbix-ops-backend.service`)
- **Database:** PostgreSQL (dedicated, isolated from Zabbix DB)
