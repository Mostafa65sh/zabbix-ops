from pydantic import BaseModel


class AlertAnalyticsStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
