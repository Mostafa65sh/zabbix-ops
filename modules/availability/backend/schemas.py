from pydantic import BaseModel


class AvailabilityStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
