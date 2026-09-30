from pydantic import BaseModel


class AIAndIntelligenceStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
