from pydantic import BaseModel


class NetworkOperationsStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
