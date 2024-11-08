from pydantic import BaseModel

class Collection(BaseModel):
    collection_name: str
    description: str

class CollectionResponse(BaseModel):
    collection_id:  str  
    collection_name: str
    description: str
    