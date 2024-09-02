# config.py
import pymysql.cursors
import os
import boto3
from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security import OAuth2PasswordBearer


DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_DATABASE'),
    'cursorclass': pymysql.cursors.DictCursor
}

load_dotenv()

cognito_client = boto3.client('cognito-idp', region_name='eu-north-1')
user_pool_id=os.getenv('user_pool_id')
client_id=os.getenv('client_id')

S3_BUCKET = os.getenv('S3_BUCKET')
s3_client = boto3.client('s3')



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
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