from pydantic import BaseModel


class DashboardBuilderStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
