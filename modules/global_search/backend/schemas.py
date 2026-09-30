from pydantic import BaseModel


class GlobalSearchStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
