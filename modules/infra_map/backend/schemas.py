from pydantic import BaseModel


class InfrastructureMapStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
