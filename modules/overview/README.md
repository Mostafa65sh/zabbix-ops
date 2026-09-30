# Module 01 — Overview

## Description
Enterprise operations overview and observability layer. Provides an evidence-based operational summary of infrastructure health, host states, active incidents, measured availability, top problem hosts, and chronological event audit.

## Module ID
`overview`

## Version
`1.0.0`

## API Namespace
`/api/v1/overview`

## Declared Permissions
- `module.overview.view` (Enforced on all module endpoints)

## Status
**Phase 1 Complete — Operational Reference Module**

---

## Architectural Flow
```text
Browser (OverviewPage)
       ↓  HTTP / REST
FastAPI Core (/api/v1/overview)
       ↓  OverviewService
Zabbix Adapter (MockZabbixAdapter | RealZabbixAdapter)
       ↓  JSON-RPC 2.0
Zabbix 7.0.5 Monitoring Engine
```

---

## Backend Endpoints

### 1. `GET /api/v1/overview`
Main operational telemetry endpoint. Protected by `require_permission("module.overview.view")`.

**Query Parameters:**
- `time_range`: `5m`, `15m`, `1h`, `6h`, `24h` (default), `7d`, `30d`.
- `group`: Filter by host group (e.g. `Linux Servers`, `Database Cluster`, `Network Devices`).
- `severity`: Filter by severity integer (`1` to `5`).
- `status`: Filter by host status (`UP`, `DOWN`, `MAINTENANCE`).
- `host`: Search/filter by host name.

**Response Contract (`OverviewResponseDTO`):**
- `generated_at`: ISO UTC timestamp.
- `time_range`: Start and end epoch timestamps with range code.
- `health`: Evidence-based status (`HEALTHY`, `DEGRADED`, `CRITICAL`, `UNKNOWN`), reason key, and human-readable evidence list.
- `hosts`: Count breakdown (`total`, `available`, `unavailable`, `unknown`, `maintenance`).
- `problems`: Severity breakdown (`total`, `disaster`, `high`, `average`, `warning`, `information`).
- `availability`: Measured availability percentage (`%`), planned maintenance seconds, unplanned downtime seconds, and lineage definition.
- `active_problems`: Normalized problem list with duration, severity badges, and acknowledgment status.
- `top_problem_hosts`: Ranked list of hosts with problem counts, highest severity, and oldest incident duration.
- `recent_events`: Chronological incident and recovery timeline.
- `infrastructure`: Categorized infrastructure domains with explicit `NO_DATA` for unmonitored domains.
- `trend`: Net incident trajectory (`improving`, `stable`, `degrading`, `unknown`).
- `data_lineage`: Traceability metadata and data integrity rules.

### 2. `GET /api/v1/overview/status`
Health check and readiness status for the module.

---

## Frontend Components (`modules/overview/frontend/`)
- `OverviewPage`: Main coordinating page with auto-refresh (off, 30s, 60s, 5m), non-blocking error handling, and theme state.
- `OverviewHeader`: Environment indicator, manual refresh button with last updated timestamp, theme toggle, and user area.
- `OverviewFilterBar`: Interactive time window buttons, group/severity/status dropdowns, search input, and auto-refresh selector.
- `HealthSummary`: 4 dense operational KPI cards with evidence-based status and clickable drill-down filters.
- `ActiveProblemsTable`: Dense operational table with sorting, local search, severity dots, and duration pills.
- `TopProblemHosts`: Hosts ranked by incident count and highest severity.
- `InfrastructureStatus`: Domain health cards explicitly distinguishing monitored from unmonitored domains.
- `RecentEventsTimeline`: Chronological operational events audit log.

---

## Golden Data Integrity Principles Enforced
1. **No Data != Healthy**: Unmonitored domains (e.g., Cloud) are explicitly shown as `NO SOURCE CONFIGURED` with status `NO_DATA`.
2. **Missing Telemetry != 100% Availability**: When no hosts match query filters, availability returns `null` (displayed as `N/A`) rather than a fabricated `100%` or `0%`.
3. **No Arbitrary Health Scores**: Health is evaluated directly from active disaster/high incidents and unreachable hosts.
