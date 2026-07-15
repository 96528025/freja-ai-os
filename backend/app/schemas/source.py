from datetime import datetime

from pydantic import BaseModel


class SourceDefinitionRead(BaseModel):
    id: str
    name: str
    description: str
    kind: str
    acquisition: str
    auth_mode: str
    availability: str
    enabled: bool
    health: str
    last_error: str | None
    last_success_at: datetime | None


class SourceUpdate(BaseModel):
    enabled: bool

