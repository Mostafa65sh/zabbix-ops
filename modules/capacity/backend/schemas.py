from pydantic import BaseModel


class CapacityPlanningStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
