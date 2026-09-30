from pydantic import BaseModel


class ServicesStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
