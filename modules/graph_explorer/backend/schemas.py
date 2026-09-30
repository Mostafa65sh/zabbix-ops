from pydantic import BaseModel


class GraphExplorerStatusResponse(BaseModel):
    module: str
    name: str
    status: str
    version: str
