from fastapi import APIRouter, HTTPException, Depends
from models.resource_models import Resource
from services.resource_service import add_resource_service, get_resources_service, delete_resource_service
from typing import List
from config import get_current_user

router = APIRouter()

@router.post("/add_resource", response_model=dict)
async def create_resource(resource: Resource, current_user: dict = Depends(get_current_user)):
    return add_resource_service(resource)

@router.get("/resources/{collection_id}", response_model=dict)
async def read_resources(collection_id: str, current_user: dict = Depends(get_current_user)):
    return get_resources_service(collection_id)

@router.delete("/delete_resource", response_model=dict)
async def remove_resource(collection_id: str, resource_id: str, current_user: dict = Depends(get_current_user)):
    return delete_resource_service(collection_id, resource_id)