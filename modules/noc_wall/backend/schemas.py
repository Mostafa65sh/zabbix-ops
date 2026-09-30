from pydantic import BaseModel


class NOCWallStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
