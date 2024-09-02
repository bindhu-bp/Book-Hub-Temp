from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import pymysql.cursors
import hashlib
from database import get_db_connection
from models import LoginRequest, SignupRequest, ResetPasswordRequest, CognitoEvent
from events.publisher import publish_event
import json
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Security
from config import cognito_client, user_pool_id,client_id
from botocore.exceptions import ClientError


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# AWS Cognito client

# Utility function to verify token with Cognito
def verify_cognito_token(token: str):
    try:
        response = cognito_client.get_user(AccessToken=token)
        return response
    except cognito_client.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Dependency to get the current user
async def get_current_user(token: str = Security(oauth2_scheme)):
    return verify_cognito_token(token)

# Global variable to keep track of the logged-in user
# logged_in_user = None

# # Password hashing and verification functions
# def hash_password(password: str) -> str:
#     return hashlib.sha256(password.encode()).hexdigest()

# def verify_password(stored_hash: str, password: str) -> bool:
#     return stored_hash == hash_password(password)

# @router.post("/login")
# async def login(request: LoginRequest):
#     global logged_in_user
#     connection = get_db_connection()
#     if not connection:
#         return {"statusCode": 500, "message": "Database connection error"}
    
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT * FROM users WHERE email_id = %s", (request.email_id,))
#             result = cursor.fetchone()

#             if not result:
#                 return {"statusCode": 400, "message": "User not found, Signup to proceed"}

#             if verify_password(result['password'], request.password):
#                 logged_in_user = result['name']
#                 # publish_event('UserLoggedIn', {'email_id': request.email_id})
#                 return {"statusCode": 200, "message": "Login successful", "email_id": result['email_id'], "name": result['name'], "role": result['role']}
#             else:
#                 return {"statusCode": 401, "message": "Invalid email or password"}
#     finally:
#         connection.close()

# @router.post("/signup")
# async def signup(request: SignupRequest):
#     hashed_password = hash_password(request.password)
#     # user_data = request.dict()
#     role = 'admin' if request.email_id in ['alam@montycloud.com', 'bindhu@montycloud.com'] else 'visitor'
    
#     connection = get_db_connection()
#     if not connection:
#         return {"statusCode": 500, "message": "Database connection error"}

#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT * FROM users WHERE email_id = %s", (request.email_id,))
#             if cursor.fetchone():
#                 return {"statusCode": 400, "message": "User already exists. Please login to proceed."}
            
#             cursor.execute("INSERT INTO users (name, email_id, password, role) VALUES (%s, %s, %s, %s)", (request.name, request.email_id, hashed_password, role))
#             connection.commit()
#             # publish_event('UserCreated', request.email_id)
#             return {"statusCode": 200, "message": "User registered successfully"}
#     finally:
#         connection.close()

# @router.post("/reset-password")
# async def reset_password(request: ResetPasswordRequest):
#     connection = get_db_connection()
#     if not connection:
#         return {"statusCode": 500, "message": "Database connection error"}
    
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT * FROM users WHERE email_id = %s", (request.email_id,))
#             if not cursor.fetchone():
#                 return {"statusCode": 404, "message": "Email not found"}

#             hashed_password = hash_password(request.new_password)
#             cursor.execute("UPDATE users SET password = %s WHERE email_id = %s", (hashed_password, request.email_id))
#             connection.commit()
#             publish_event('PasswordReset', {'email_id': request.email_id, 'new_password': hashed_password})
#             return {"statusCode": 200, "message": "Password reset successfully"}
#     finally:
#         connection.close()


@router.post("/test_users")
async def lambda_handler(event: CognitoEvent):
    try:
        # Connect to the database
        conn = get_db_connection()
    except:
        print("ERROR: Could not connect to MySQL instance.")
        return {
            'statusCode': 500,
            'body': json.dumps('Database connection failed')
        }
    try:
        with conn.cursor() as cur:
            # Extract user data from the Cognito event
            user_id = event.request['userAttributes']['sub']
            name = event.request['userAttributes']['name']
            email = event.request['userAttributes']['email']
            # Insert user data into the database
            sql = "INSERT INTO test_users (cognito_user_id, name, email) VALUES (%s, %s, %s)"
            cur.execute(sql, (user_id, name, email))
            conn.commit()
        return {
            'statusCode': 200,
            'body': json.dumps('User data stored in RDS successfully')
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error storing user data: {str(e)}')
        }
    finally:
        conn.close()

@router.post("/login")
async def login(request: LoginRequest):
    try:
        response = cognito_client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': request.email_id,
                'PASSWORD': request.password
            },
            ClientId=client_id
        )
        
        id_token = response['AuthenticationResult']['IdToken']
        access_token = response['AuthenticationResult']['AccessToken']

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email_id = %s", (request.email_id,))
                result = cursor.fetchone()
                if result:
                    return {"statusCode": 200, "message": "Login successful","user_id":result['user_id'], "email_id": result['email_id'], "name": result['name'], "role": result['role'], "id_token": id_token, "access_token": access_token}
                else:
                    return {"statusCode": 400, "message": "User not found in local database"}
        finally:
            connection.close()
    except ClientError as e:
        if e.response['Error']['Code'] == 'NotAuthorizedException':
            raise HTTPException(status_code=401, detail="Invalid email or password")
        else:
            raise HTTPException(status_code=500, detail="Error during authentication")
        

@router.post("/signup")
async def signup(request: SignupRequest):
    try:
        print(request)
        print("calling cognito")
        try:
            response = cognito_client.sign_up(
                ClientId=client_id,
                Username=request.email_id,
                Password=request.password,
                UserAttributes=[
                    {'Name': 'email', 'Value': request.email_id},
                    {'Name': 'name', 'Value': request.name}
                ]
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'UsernameExistsException':
                raise HTTPException(status_code=400, detail="User already exists. Please login to proceed.")
            else:
                raise HTTPException(status_code=500, detail="Error during signup")

        cognito_client.admin_confirm_sign_up(
            UserPoolId=user_pool_id,
            Username=request.email_id
        )
        user_details = cognito_client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=request.email_id
        )
        sub = next(attr['Value'] for attr in user_details['UserAttributes'] if attr['Name'] == 'sub')
        
        role = 'admin' if request.email_id in ['alam@montycloud.com', 'bindhu@montycloud.com'] else 'visitor'

        connection = get_db_connection()
        if not connection:
            return {"statusCode": 500, "message": "Database connection error"}

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email_id = %s", (request.email_id,))
                if cursor.fetchone():
                    return {"statusCode": 400, "message": "User already exists. Please login to proceed."}

                cursor.execute("INSERT INTO users (user_id, name, email_id, role) VALUES (%s, %s, %s, %s)", (sub, request.name, request.email_id, role))
                connection.commit()
                return {"statusCode": 200, "message": "User registered successfully"}
        finally:
            connection.close()
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'UsernameExistsException':
            raise HTTPException(status_code=400, detail="User already exists. Please login to proceed.")
        else:
            raise HTTPException(status_code=500, detail="Error during signup")