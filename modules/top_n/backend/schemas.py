from pydantic import BaseModel


class TopNStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
