from pydantic import BaseModel


class Host360StatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
