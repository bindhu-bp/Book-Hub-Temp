from fastapi import APIRouter, HTTPException, Depends
from models.collection_models import Collection, CollectionResponse
from services.collection_service import (
    create_collection_service,
    delete_collection_service,
    get_collections_service,
)
from typing import List
from config import get_current_user


router = APIRouter()

@router.post("/add_collection", response_model=dict )
def create_collection(collection: Collection, current_user: dict = Depends(get_current_user)):
    return create_collection_service(collection)

@router.delete("/delete_collection/{collection_id}", response_model=dict)
def delete_collection(collection_id: str, current_user: dict = Depends(get_current_user)):
    return delete_collection_service(collection_id)

@router.get("/collections",  response_model=List[CollectionResponse])
def get_collections(current_user: dict = Depends(get_current_user)):
    return get_collections_service()


