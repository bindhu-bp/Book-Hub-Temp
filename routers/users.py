from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import pymysql.cursors
from database import get_db_connection
from models import UserUpdateRequest
from config import get_current_user

router = APIRouter()

#
@router.get("/list-users")
async def list_users():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT email_id, name, role FROM users")
            users = cursor.fetchall()
            return {"users": users}
    except pymysql.Error as e:
        print(f"Database error: {e}")
        return {"message": "Database error"}, 500
    finally:
        connection.close()


@router.post("/update-role")
async def update_role(request: UserUpdateRequest):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE users SET role = %s WHERE email_id = %s", (request.role, request.email_id))
            if cursor.rowcount == 0:
                return {"message": "User not found"}, 404
            connection.commit()
            return {"message": "Role updated successfully"}, 200
    except pymysql.Error as e:
        print(f"Database error: {e}")


        return {"message": "Database error"}, 500
    finally:
        connection.close()
