from pydantic import BaseModel


class DatabaseOperationsStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
