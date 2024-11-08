from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class Resource(BaseModel):
    resource_id: Optional[UUID] = None
    resource_name: str
    description: str
    link: str
    collection_id: str 

