from pydantic import BaseModel


class ReportsStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
