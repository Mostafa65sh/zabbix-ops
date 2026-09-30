from pydantic import BaseModel


class ApplicationsStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
