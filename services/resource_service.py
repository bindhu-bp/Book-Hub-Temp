
from typing import List
from database import get_db_connection
from models.resource_models import Resource
from fastapi import HTTPException
from queries.resource_queries import ResourceQueries
import uuid

def add_resource_service(resource: Resource) -> dict:
    resource_id = str(uuid.uuid4())
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(ResourceQueries.check_resource_exists(), (resource.link, resource.collection_id))
            if cursor.fetchone()['count'] > 0:
                raise HTTPException(status_code=409, detail="Resource already exists")

            cursor.execute(ResourceQueries.insert_resource(), (resource_id, resource.resource_name, resource.link, resource.description, resource.collection_id))
            connection.commit()
        return {"message": "Resource added successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding resource: {str(e)}")
    finally:
        connection.close()

def get_resources_service(collection_id: str) -> dict:
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(ResourceQueries.get_resources_by_collection(), (collection_id,))
            result = cursor.fetchall()
            if not result:
                raise HTTPException(status_code=404, detail="No resources found for this collection")

            resources = [
                Resource(
                    resource_id=row["resource_id"],
                    resource_name=row["resource_name"],
                    link=row["link"],
                    description=row["description"],
                    collection_id=collection_id  
                ) 
                for row in result
            ]

            return {
                "collection_id": collection_id,
                "resources": resources
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving resources: {str(e)}")
    finally:
        connection.close()


def delete_resource_service(collection_id: str, resource_id: str) -> dict:
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(ResourceQueries.delete_resource(), (collection_id, resource_id))
            connection.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Resource not found")
        return {"message": "Resource deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting resource: {str(e)}")
    finally:
        connection.close()
