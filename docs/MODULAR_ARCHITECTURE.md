# Zabbix Operations Platform — Modular Architecture Specification

## 1. Architectural Overview

The **Zabbix Operations UI** follows a strict **Core + Installable Modules** architecture.

- **Non-Invasive**: The system does not modify Zabbix source code or database schemas. All interaction with Zabbix is performed strictly via JSON-RPC 2.0 through the Core `ZabbixAdapterBase` (Mock & Real implementations).
- **Offline-First**: Production environments have **no direct internet access**. Modules are designed as self-contained installable packages deployed offline.
- **Single-App Runtime**: Modules are logically and structurally isolated within a unified FastAPI backend and React frontend application runtime—avoiding unnecessary microservices or distributed systems complexity.

```text
                        ┌─────────────────────────────────────┐
                        │      Zabbix 7.0.5 Monitoring Engine │
                        └──────────────────┬──────────────────┘
                                           │ JSON-RPC (api_jsonrpc.php)
                        ┌──────────────────▼──────────────────┐
                        │           OPERATIONS CORE           │
                        │                                     │
                        │  • Configuration (Settings)         │
                        │  • Auth & RBAC (User, Permissions)  │
                        │  • Central Logging ([module=<id>])  │
                        │  • Zabbix Adapter Layer             │
                        │  • Shared PostgreSQL Database       │
                        │  • Module Manager & Registry        │
                        └──────────────────┬──────────────────┘
                                           │
          ┌────────────────┬───────────────┼───────────────┬────────────────┐
          │                │               │               │                │
    ┌─────▼─────┐    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐    ┌─────▼─────┐
    │  Module   │    │  Module   │   │  Module   │   │  Module   │    │  Module   │
    │  Overview │    │  Servers  │   │  Problems │   │  Topology │    │  Reports  │
    └───────────┘    └───────────┘   └───────────┘   └───────────┘    └───────────┘
```

---

## 2. Core Responsibilities

Core provides platform infrastructure and shared utilities only. Modules must NEVER duplicate these services:

1. **Authentication (`app.core.auth`)**:
   - Central authentication abstraction (`BaseAuthProvider`, `LocalDevAuthProvider`).
   - Standard user model (`User`) and FastAPI dependency (`get_current_user`).
   - Permission validation utilities (`has_permission`, `require_permission`).
2. **Configuration (`app.core.config`)**:
   - Shared platform environment variables (database connection, Zabbix URL, adapter type, core version).
   - Module directory location (`MODULES_DIR`) and filter lists (`ENABLED_MODULES`, `DISABLED_MODULES`).
   - Module-specific configuration belongs strictly inside each module.
3. **Logging (`app.core.logging`)**:
   - Centralized logging configuration (`setup_logging`).
   - Automatic module tagging (`[module=<id>]`) via `get_module_logger(module_id)`.
4. **Zabbix Adapter (`app.adapters.zabbix`)**:
   - `MockZabbixAdapter`: Used in local development and CI testing.
   - `RealZabbixAdapter`: Used in production with live Zabbix 7.0.5 servers.
   - Modules never establish direct HTTP connections to Zabbix.

---

## 3. Module Contract & Directory Structure

Every module resides in `modules/<module_id>/` and conforms to the following contract:

```text
modules/<module_id>/
├── manifest.json            # Module manifest & dependency specification
├── permissions.json         # Declared RBAC permissions
├── README.md                # Module purpose, API prefix, and docs
├── backend/
│   ├── __init__.py
│   ├── routes.py            # APIRouter mounted at /api/v1/<module_id>
│   ├── services.py          # Business logic services
│   ├── schemas.py           # Pydantic DTOs & response schemas
│   └── models.py            # SQLAlchemy models (shared DB session)
├── frontend/
│   ├── index.ts             # Module definition for FrontendModuleRegistry
│   ├── routes.tsx           # React UI components and route views
│   └── components/          # Reusable module-specific components
├── migrations/              # Alembic schema migrations
└── tests/
    ├── __init__.py
    └── test_skeleton.py     # Module test suite
```

---

## 4. Module Manifest Schema

Each module specifies its metadata and requirements in `manifest.json`:

```json
{
  "id": "overview",
  "name": "Overview",
  "version": "0.1.0",
  "description": "Infrastructure operations overview, KPIs, and health status",
  "core_version": ">=0.2.0",
  "enabled_by_default": true,
  "dependencies": [],
  "optional_dependencies": [],
  "permissions": ["module.overview.view"],
  "backend_entry": "modules.overview.backend.routes:router",
  "frontend_entry": "index.ts",
  "author": "Zabbix Operations Team",
  "tags": ["overview", "operations"]
}
```

### Lifecycle Statuses:
- `DISCOVERED`: Manifest detected on filesystem.
- `ENABLED`: Validated, compatible, and configured to load.
- `DISABLED`: Deactivated via `.env` or manifest setting without removing code.
- `LOADED`: Backend router dynamically mounted and available.
- `INCOMPATIBLE`: Current Core version does not satisfy `core_version` constraint.
- `DEPENDENCY_ERROR`: Missing or disabled required dependencies.
- `ERROR`: Unhandled exception or syntax error during registration.

---

## 5. Module Manager (`app.core.modules.manager`)

The `ModuleManager` orchestrates module lifecycle:
1. **Discovery**: Iterates `modules/` directory and parses `manifest.json`.
2. **Version Compatibility**: Checks Core semver constraints (`>=`, `<=`, `==`, `^`, `*`).
3. **Configuration Check**: Evaluates `DISABLED_MODULES` and `ENABLED_MODULES`.
4. **Dependency Resolution**: Ensures required dependency modules exist and are active.
5. **Route Mounting**: Dynamically attaches module routers at `/api/v1/<module_id>`.
6. **API Inventory**:
   - `GET /api/v1/system/modules`: Full status list of all platform modules.
   - `GET /api/v1/system/info`: Platform metadata, Core version, and module counts.

---

## 6. Frontend Module Registry (`frontend/src/modules/registry.ts`)

In the React frontend, modules register through `moduleRegistry`:
- Modules register route, navigation item (label, icon, order), and permissions.
- Navigation bar dynamically builds navigation from enabled modules sorted by `order`.
- When a module is disabled, its navigation item and routes are withheld.

---

## 7. Product Module Roadmap (21 Modules)

| # | Module ID | Name | Core Purpose |
|---|-----------|------|--------------|
| 01 | `overview` | Overview | Infrastructure operations overview & KPIs |
| 02 | `servers` | Servers | Server inventory, hardware & OS management |
| 03 | `problems` | Problems | Problem Center & acknowledgment workflow |
| 04 | `availability`| Availability | SLA availability & downtime timeline |
| 05 | `host360` | Host 360 | 360-degree host telemetry & event overlays |
| 06 | `top_n` | Top N | Ranked utilization (CPU, memory, disk, network) |
| 07 | `graph_explorer`| Graph Explorer | Multi-series metric visualization |
| 08 | `global_search`| Global Search | Unified search across hosts, items, events |
| 09 | `network` | Network Operations | Switch/router ports, latency & packet loss |
| 10 | `database` | Database Operations | DB performance (Postgres, Oracle, MSSQL, MySQL) |
| 11 | `web_monitoring`| Web Monitoring | Web scenario health, HTTP latency & SSL/TLS |
| 12 | `services` | Services | Business & technical service SLA trees |
| 13 | `applications` | Applications | Middleware & application health |
| 14 | `capacity` | Capacity Planning | Forecasting & resource exhaustion estimation |
| 15 | `trend_detection`| Trend Detection | Anomaly candidates & baseline degradation |
| 16 | `infra_map` | Infrastructure Map | Visual topology & dependency graphs |
| 17 | `dashboards` | Dashboard Builder | Customizable NOC dashboards & widgets |
| 18 | `reports` | Reports | Scheduled and on-demand PDF/CSV reports |
| 19 | `alert_analytics`| Alert Analytics | MTTR, MTBF & noisy trigger analytics |
| 20 | `noc_wall` | NOC Wall | Fullscreen 24/7 wallboard display |
| 21 | `intelligence` | AI & Intelligence | Operational assistant & incident correlation |

---

## 8. Golden Data Integrity Rules

1. **No Data != Healthy**: Missing telemetry must never be masked as normal.
2. **No Data != 0 & No Data != 100%**: Missing metrics must be represented as `N/A`.
3. **Explainable Calculations**: Every availability percentage and capacity forecast must disclose its exact formula and item sources.
4. **Offline Isolation**: All assets and packages must build without internet connectivity during production deployment.
