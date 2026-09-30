import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ModuleManifest(BaseModel):
    id: str = Field(..., description="Unique alphanumeric identifier for the module (e.g. 'overview')")
    name: str = Field(..., description="Human-readable module name")
    version: str = Field(..., description="Semantic version string (e.g. '0.1.0')")
    description: str = Field(default="", description="Brief description of the module")
    core_version: str = Field(default=">=0.2.0", description="Compatible Core semver range (e.g. '>=0.2.0')")
    enabled_by_default: bool = Field(default=True, description="Whether module is enabled by default")
    dependencies: List[str] = Field(default_factory=list, description="Required module IDs")
    optional_dependencies: List[str] = Field(default_factory=list, description="Optional module IDs")
    permissions: List[str] = Field(default_factory=list, description="Declared permissions (e.g. 'module.overview.view')")
    backend_entry: Optional[str] = Field(default=None, description="Python import path to backend APIRouter")
    frontend_entry: Optional[str] = Field(default=None, description="Frontend entry point (e.g. 'index.ts')")
    author: Optional[str] = Field(default="Zabbix Operations Team")
    tags: List[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_module_id(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_]+$", v):
            raise ValueError(f"Module ID '{v}' must be lowercase alphanumeric with underscores only.")
        return v
