from pydantic import BaseModel


class TrendDetectionStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
