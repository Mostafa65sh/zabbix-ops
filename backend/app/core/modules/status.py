from enum import Enum
from typing import Optional
from pydantic import BaseModel
from app.core.modules.manifest import ModuleManifest


class ModuleStatus(str, Enum):
    DISCOVERED = "discovered"
    ENABLED = "enabled"
    DISABLED = "disabled"
    LOADED = "loaded"
    ERROR = "error"
    INCOMPATIBLE = "incompatible"
    DEPENDENCY_ERROR = "dependency_error"


class ModuleInfo(BaseModel):
    manifest: ModuleManifest
    status: ModuleStatus
    error_message: Optional[str] = None
    location: str
