from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class QueryCreate(BaseModel):
    query_text: str


class QueryRead(BaseModel):
    id: int
    query: str
    response: str
    user_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
