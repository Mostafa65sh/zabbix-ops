from pydantic import BaseModel


class WebMonitoringStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
