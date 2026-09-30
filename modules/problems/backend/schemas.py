from pydantic import BaseModel


class ProblemsStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
