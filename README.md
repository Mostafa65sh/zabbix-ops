# Zabbix Operations UI

An enterprise-grade Observability and Operations layer over **Zabbix 7.0.5**, designed for offline, manual deployment on production Linux servers.

---

## Architecture

```text
Browser (React Frontend)
       ↓
FastAPI Backend API (/ops-api)
       ↓
Zabbix Adapter (RealZabbixAdapter / MockZabbixAdapter)
       ↓
Zabbix 7.0.5 API (api_jsonrpc.php)
```

---

## Directory Structure

```text
zabbix-ops/
├── backend/
│   ├── app/
│   │   ├── adapters/zabbix/     # Real & Mock Zabbix JSON-RPC adapters
│   │   ├── api/v1/              # Versioned API routes (health, overview, hosts, problems)
│   │   ├── core/                # Configuration and environment settings
│   │   ├── models/              # Pydantic schemas and DTOs
│   │   └── main.py              # FastAPI application entry point
│   ├── tests/                   # Pytest test suite
│   ├── requirements.txt         # Pinned Python dependencies
│   └── pyproject.toml           # Project metadata
│
├── frontend/
│   ├── src/                     # React + TypeScript source
│   ├── dist/                    # Compiled production build
│   └── package.json             # NPM dependencies
│
├── deployment/
│   ├── apache/                  # Apache reverse proxy virtual host configuration
│   ├── systemd/                 # systemd service unit file
│   ├── database/                # Schema migrations
│   └── scripts/                 # Offline deployment and release packaging scripts
│
├── config/
│   └── .env.example             # Configuration template
│
└── docs/
    └── ARCHITECTURE.md          # Architectural specification
```

---

## Local Development (Phase 0)

### Frontend (React + TypeScript + Vite)
```bash
cd zabbix-ops/frontend
npm install
npm run dev      # Local dev server at http://localhost:5173
npm run build    # Produces optimized dist/
```

### Backend (FastAPI + Python)
```bash
cd zabbix-ops/backend
python -m venv venv
source venv/bin/activate       # On Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
