from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging, get_module_logger
from app.core.modules.manager import module_manager
from app.api.v1 import health, overview, hosts, problems, system

setup_logging()
logger = get_module_logger("core")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Platform ready with {len(module_manager.get_modules())} discovered modules.")
    yield
    logger.info("Shutting down Operations Platform.")


app = FastAPI(
    title="Zabbix Operations UI - Backend API",
    description="Enterprise Observability & Operations Layer for Zabbix 7.0.5",
    version=settings.CORE_VERSION,
    lifespan=lifespan
)

# CORS middleware for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Core system routes
app.include_router(system.router, prefix="/api/v1")

# Register legacy v1 API routes (preserved for Phase 0 compatibility)
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(hosts.router, prefix="/api/v1", tags=["Hosts"])


# Initialize module discovery and route registration
module_manager.discover_and_register(app)


@app.get("/")
async def root():
    return {
        "service": "Zabbix Operations UI API",
        "version": settings.CORE_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
        "system_modules": "/api/v1/system/modules"
    }
