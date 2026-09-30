from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import health, overview, hosts, problems

app = FastAPI(
    title="Zabbix Operations UI - Backend API",
    description="Enterprise Observability & Operations Layer for Zabbix 7.0.5",
    version="0.1.0"
)

# CORS middleware for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register v1 API routes
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(overview.router, prefix="/api/v1", tags=["Overview"])
app.include_router(hosts.router, prefix="/api/v1", tags=["Hosts"])
app.include_router(problems.router, prefix="/api/v1", tags=["Problems"])


@app.get("/")
async def root():
    return {
        "service": "Zabbix Operations UI API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
