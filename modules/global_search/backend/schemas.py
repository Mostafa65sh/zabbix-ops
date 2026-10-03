from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class GlobalSearchStatusResponse(BaseModel):
    module: str = "global_search"
    name: str = "Global Search"
    status: str = "operational"
    version: str = "1.0.0"
    declared_permission: str = "module.global_search.view"


class HostSearchResultDTO(BaseModel):
    id: str
    name: str
    host: str
    ip: str = ""
    status: str
    groups: List[str] = Field(default_factory=list)
    os: Optional[str] = None
    problems_count: int = 0


class ProblemSearchResultDTO(BaseModel):
    eventid: str
    name: str
    severity: int
    clock: int
    acknowledged: bool
    host_name: str
    host_id: str
    opdata: Optional[str] = None


class ServiceSearchResultDTO(BaseModel):
    serviceid: str
    name: str
    status: int
    description: Optional[str] = None
    tags: List[Dict[str, str]] = Field(default_factory=list)


class ItemSearchResultDTO(BaseModel):
    itemid: str
    name: str
    key_: str
    host_name: str
    host_id: str
    lastvalue: Optional[Any] = None
    units: str = ""


class HostCategoryResultDTO(BaseModel):
    items: List[HostSearchResultDTO] = Field(default_factory=list)
    total_matched: int = 0
    is_truncated: bool = False


class ProblemCategoryResultDTO(BaseModel):
    items: List[ProblemSearchResultDTO] = Field(default_factory=list)
    total_matched: int = 0
    is_truncated: bool = False


class ServiceCategoryResultDTO(BaseModel):
    items: List[ServiceSearchResultDTO] = Field(default_factory=list)
    total_matched: int = 0
    is_truncated: bool = False


class ItemCategoryResultDTO(BaseModel):
    items: List[ItemSearchResultDTO] = Field(default_factory=list)
    total_matched: int = 0
    is_truncated: bool = False


class SearchCategoriesDTO(BaseModel):
    hosts: HostCategoryResultDTO = Field(default_factory=HostCategoryResultDTO)
    problems: ProblemCategoryResultDTO = Field(default_factory=ProblemCategoryResultDTO)
    services: ServiceCategoryResultDTO = Field(default_factory=ServiceCategoryResultDTO)
    items: ItemCategoryResultDTO = Field(default_factory=ItemCategoryResultDTO)


class GlobalSearchResponseDTO(BaseModel):
    query: str
    timestamp: int
    categories: SearchCategoriesDTO = Field(default_factory=SearchCategoriesDTO)
    total_results: int = 0
