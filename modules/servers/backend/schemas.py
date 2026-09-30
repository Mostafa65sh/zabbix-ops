from pydantic import BaseModel


class ServersStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
