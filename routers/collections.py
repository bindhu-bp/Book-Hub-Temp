from fastapi import APIRouter
from typing import List
import pymysql.cursors
from database import get_db_connection
from models import Collection, SubscriptionRequest
from events.publisher import publish_event, subscribe_user
from fastapi import HTTPException, Depends,Security
from fastapi.security import OAuth2PasswordBearer
from config import cognito_client,get_current_user


router = APIRouter()


@router.post("/add_collection", status_code=201)
async def create_collection(collection: Collection):
    if not collection.collection_name.strip():
        return {"message": "Collection name cannot be empty"}, 400

    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS count FROM collection WHERE collection_name = %s", (collection.collection_name,))
        result = cursor.fetchone()

        if result['count'] > 0:
            return {"message": "The collection already exists."}, 409

        cursor.execute("INSERT INTO collection (collection_name) VALUES (%s)", (collection.collection_name,))
        connection.commit()

        # publish_event('CollectionCreated', {'collection_name': collection.collection_name})

    connection.close()
    return {"message": "Collection added successfully."}, 201


# Delete a collection
@router.delete("/delete_collection/{collection_name}")
async def delete_collection(collection_name: str):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM collection WHERE collection_name = %s", (collection_name,))
            result = cursor.fetchone()
            if result['count'] == 0:
                return {"message": "Collection not found"}, 404

            cursor.execute("DELETE FROM resources WHERE collection_name = %s", (collection_name,))
            cursor.execute("DELETE FROM collection WHERE collection_name = %s", (collection_name,))
            connection.commit()

            # try:
            #     publish_event('CollectionDeleted', {'collection_name': collection_name})
            # except Exception:
            #     # If event publishing fails, we'll still return success for collection deletion
            #     pass

            return {"message": "Collection and its resources deleted successfully"}, 204

    except pymysql.MySQLError as e:
        return {"message": f"Database error: {str(e)}"}, 500
    except Exception as e:
        return {"message": f"An unexpected error occurred: {str(e)}"}, 500
    finally:
        connection.close()

# Get a list of collections
@router.get("/collections_list")
async def get_collections():
    connection = get_db_connection()
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT collection_name FROM collection")
            result = cursor.fetchall()
            return [{"collection_name": row["collection_name"]} for row in result], 200
    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}, 500
    finally:
        connection.close()

# Get resources for a collection
@router.get("/collections_list/{collection_name}/resources")
async def get_resources(collection_name: str, ):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT resource_name, link, description FROM resources WHERE collection_name = %s AND resource_name != ''", (collection_name,))
            result = cursor.fetchall()
            if not result:
                return {"message": "No resources found for this collection"}, 404
            return [{"resource_name": row["resource_name"], "link": row["link"], "description": row["description"]} for row in result], 200
    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}, 500
    finally:
        connection.close()

# Subscribe to the get notified
@router.post("/subscribe")
async def subscribe(subscription: SubscriptionRequest):
    try:
        response = subscribe_user(subscription.email)
        return {"message": "Subscription successful", "response": response}, 200
    except Exception as e:
        return {"message": f"Subscription failed: {str(e)}"}, 400