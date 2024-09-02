from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import pymysql.cursors
from database import get_db_connection
from models import Resource
from events.publisher import publish_event
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Security
from config import cognito_client,get_current_user


router = APIRouter()

# Get collection names
@router.get("/collections")
def get_collection_names():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT collection_name FROM collection")
            collection = [row['collection_name'] for row in cursor.fetchall()]
        return {"collections": collection}
    except Exception as e:
        print(f"Error fetching collection: {e}")
        return {"message": "Failed to fetch collections"}, 500
    finally:
        connection.close()

# Add a resource to the collection
@router.post("/add_resource")
async def create_resource(resource: Resource):
    if not resource.resource_name.strip():
        return {"message": "Resource name cannot be empty"}, 400
    if not resource.link.strip():
        return {"message": "Resource link cannot be empty"}, 400
    if not resource.collection_name.strip():
        return {"message": "Collection name cannot be empty"}, 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS count FROM resources WHERE link = %s AND collection_name = %s", 
                (resource.link, resource.collection_name)
            )
            result = cursor.fetchone()
            if result['count'] > 0:
                return {"message": "Resource already exists"}, 409

            cursor.execute(
                "INSERT INTO resources (resource_name, link, description, collection_name) VALUES (%s, %s, %s, %s)",
                (resource.resource_name, resource.link, resource.description, resource.collection_name)
            )
            connection.commit()

            # publish_event('ResourceAdded', {'resource_name': resource.resource_name, 'collection_name': resource.collection_name})
            
        return {"message": "Resource added successfully"}, 201
    except Exception as e:
        print(f"Error adding resource: {e}")


        return {"message": "Failed to add resource. Please try again later."}, 500
    finally:
        connection.close()

# Delete a resource
@router.delete("/delete_resource/{collection_name}/{resource_name}")
async def delete_resource(collection_name: str, resource_name: str):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM resources WHERE collection_name = %s AND resource_name = %s", (collection_name, resource_name))
            connection.commit()

            # publish_event('ResourceDeleted', {'collection_name': collection_name, 'resource_name': resource_name})
            
            if cursor.rowcount == 0:
                return {"message": "Resource not found"}, 404
            return {"message": "Resource deleted successfully"}, 200
    finally:
        connection.close()
