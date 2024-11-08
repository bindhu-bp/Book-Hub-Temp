from database import get_db_connection
from fastapi import HTTPException
from botocore.exceptions import ClientError 
from config import cognito_client, user_pool_id
from models.user_models import EditProfileRequest

def list_users_service() -> dict:
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT email_id, name, role FROM users")
            users = cursor.fetchall()
            return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving users: {str(e)}")
    finally:
        connection.close()


def update_role_service(email_id: str, role: str) -> dict:
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE users SET role = %s WHERE email_id = %s", (role, email_id))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")
            connection.commit()
            return {"message": "Role updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating role: {str(e)}")
    finally:
        connection.close()

def delete_user_service(email_id: str) -> dict:
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Delete user from the database
            cursor.execute("DELETE FROM users WHERE email_id = %s", (email_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found in the database")

            # Delete user from the Cognito User Pool
            cognito_client.admin_delete_user(
                UserPoolId=user_pool_id,
                Username=email_id
            )

            connection.commit()

            return {"message": "User deleted successfully from both database and user pool"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user from Cognito: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user from database: {str(e)}")
    finally:
        connection.close()


def edit_user_profile_service(request: EditProfileRequest, user_id: str) -> dict:
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Check if user exists
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            old_name = user['name']

            # Update the name for the user
            cursor.execute("UPDATE users SET name = %s WHERE user_id = %s", (request.new_name, user_id))
            connection.commit()

            # Check if the old name is in contributors before updating
            cursor.execute("SELECT contributor FROM books WHERE contributor LIKE %s", (f"%{old_name}%",))
            contributors_books = cursor.fetchall()
            if contributors_books:
                # Update contributors only if old name is found in the contributors
                for book in contributors_books:
                    cursor.execute(""" 
                        UPDATE books 
                        SET contributors = REPLACE(contributors, %s, %s) 
                        WHERE book_id = %s
                    """, (old_name, request.new_name, book['book_id']))
                connection.commit()

            # Check if the old name is in borrowers before updating
            cursor.execute("SELECT borrowers FROM books WHERE borrowers LIKE %s", (f"%{old_name}%",))
            borrowers_books = cursor.fetchall()
            if borrowers_books:
                # Update borrowers only if old name is found in the borrowers
                for book in borrowers_books:
                    cursor.execute(""" 
                        UPDATE books 
                        SET borrowers = REPLACE(borrowers, %s, %s) 
                        WHERE book_id = %s
                    """, (old_name, request.new_name, book['book_id']))
                connection.commit()

            return {"message": "Profile updated successfully. Name change reflected in books if applicable."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")
    
    finally:
        connection.close()

def get_contributed_books_service(user_id: str) -> dict:
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Fetch user name based on user_id
            cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return {"message": "User not found."}
            
            # Fetch contributed books
            cursor.execute("SELECT book_name, author FROM books WHERE contributor LIKE %s", (f"%{user_id}%",))
            books = cursor.fetchall()
            
            # Prepare the response
            response = {
                "user_id": user_id,
                "name": user["name"],
                "contributed_books": books if books else "No books contributed by the user."
            }
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving contributed books: {str(e)}")
    finally:
        connection.close()

def get_borrowed_books_service(user_id: str) -> dict:
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Fetch user name based on user_id
            cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return {"message": "User not found."}
            
            # Fetch borrowed books
            cursor.execute("SELECT book_name, author FROM books WHERE borrowers LIKE %s", (f"%{user_id}%",))
            books = cursor.fetchall()
            
            # Prepare the response
            response = {
                "user_id": user_id,
                "name": user["name"],
                "borrowed_books": books if books else "No books borrowed by the user."
            }
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving borrowed books: {str(e)}")
    finally:
        connection.close()