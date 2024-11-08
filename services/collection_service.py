
from typing import List
import uuid
from fastapi import HTTPException
from models.collection_models import Collection
from database import get_db_connection
from queries.collection_queries import CollectionQueries


def create_collection_service(collection: Collection):
    if not collection.collection_name.strip():
        raise HTTPException(status_code=400, detail="Collection name cannot be empty")
    
    if not collection.description.strip():  # Ensure description is not empty
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    collection_id = str(uuid.uuid4())

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(CollectionQueries.check_collection_exists(), (collection.collection_name,))
            result = cursor.fetchone()
            if result['count'] > 0:
                raise HTTPException(status_code=409, detail="Collection already exists.")

            cursor.execute(CollectionQueries.insert_collection(), (collection_id, collection.collection_name, collection.description))
            connection.commit()
            return {"message": "Collection added successfully.", "collection_id": collection_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        connection.close()


def delete_collection_service(collection_id: int):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(CollectionQueries.check_collection_by_id(), (collection_id,))
            result = cursor.fetchone()
            if result['count'] == 0:
                raise HTTPException(status_code=404, detail="Collection not found")

            cursor.execute(CollectionQueries.delete_resources_by_collection_id(), (collection_id,))
            cursor.execute(CollectionQueries.delete_collection_by_id(), (collection_id,))
            connection.commit()

            return {"message": "Collection and its resources deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        connection.close()


def get_collections_service() -> List[dict]:
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(CollectionQueries.get_all_collections())
            result = cursor.fetchall()
            return [{"collection_id": row["collection_id"], "collection_name": row["collection_name"], "description" : row["description"]} for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        connection.close()
