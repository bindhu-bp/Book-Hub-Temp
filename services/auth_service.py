from fastapi import HTTPException
from database import get_db_connection
from config import cognito_client, user_pool_id, client_id
from botocore.exceptions import ClientError
import json
from models.auth_models import CognitoEvent, LoginRequest, SignupRequest, ResetPasswordRequest

# Utility function to verify Cognito token
def verify_cognito_token(token: str):
    try:
        response = cognito_client.get_user(AccessToken=token)
        return response
    except cognito_client.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Lambda handler service for /test_users
def lambda_handler_service(event: CognitoEvent):
    try:
        conn = get_db_connection()
    except:
        return {'statusCode': 500, 'body': json.dumps('Database connection failed')}
    
    try:
        with conn.cursor() as cur:
            user_id = event.request['userAttributes']['sub']
            name = event.request['userAttributes']['name']
            email = event.request['userAttributes']['email']
            
            sql = "INSERT INTO test_users (cognito_user_id, name, email) VALUES (%s, %s, %s)"
            cur.execute(sql, (user_id, name, email))
            conn.commit()
            
        return {'statusCode': 200, 'body': json.dumps('User data stored in RDS successfully')}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps(f'Error storing user data: {str(e)}')}
    finally:
        conn.close()



def reset_password(request: ResetPasswordRequest):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email_id = %s", (request.email_id,))  # Use email_id
            user = cursor.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            if request.new_password != request.confirm_password:
                raise HTTPException(status_code=400, detail="Passwords do not match")

            cursor.execute("UPDATE users SET password = %s WHERE email_id = %s", (request.new_password, request.email_id))  # Use email_id
            connection.commit()

            return {"message": "Password reset successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting password: {str(e)}")
    finally:
        connection.close()

def signup_service(request: SignupRequest):
    try:
        # Check if user exists in Cognito
        try:
            user_details = cognito_client.admin_get_user(
                UserPoolId=user_pool_id, Username=request.email_id
            )
            print(f"User found in Cognito\n: {user_details}")
            raise HTTPException(status_code=400, detail="User already exists. Please login to proceed.")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code != 'UserNotFoundException':
                error_message = e.response['Error'].get('Message', 'No detailed message')
                print(f"Error Code: {error_code}, Message: {error_message}")
                raise HTTPException(status_code=500, detail=f"Error checking user existence in Cognito: {error_message}")

        # Sign up the user
        response = cognito_client.sign_up(
            ClientId=client_id,
            Username=request.email_id,
            Password=request.password,
            UserAttributes=[
                {'Name': 'email', 'Value': request.email_id},
                {'Name': 'name', 'Value': request.name}
            ]
        )
        print(f"User signed up in Cognito:\n{response}")

        # Confirm the user in Cognito
        cognito_client.admin_confirm_sign_up(
            UserPoolId=user_pool_id,
            Username=request.email_id
        )

        # Get user details from Cognito
        user_details = cognito_client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=request.email_id
        )
        sub = next(attr['Value'] for attr in user_details['UserAttributes'] if attr['Name'] == 'sub')

        admin_emails = ['alam.shaik@montycloud.com', 'Bindhu@montycloud.com']
        role = 'admin' if request.email_id in admin_emails else 'visitor'
        print(f"Assigning role '{role}' for email: {request.email_id}")

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email_id = %s", (request.email_id,))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="User already exists in the database. Please login to proceed.")

                cursor.execute(
                    "INSERT INTO users (user_id, name, email_id, role) VALUES (%s, %s, %s, %s)",
                    (sub, request.name, request.email_id, role)
                )
                connection.commit()
                return {"statusCode": 200, "message": "User registered and confirmed successfully"}
        finally:
            connection.close()

    except ClientError as e:
        # Print detailed error information for troubleshooting
        error_code = e.response['Error']['Code']
        error_message = e.response['Error'].get('Message', 'No detailed message')
        print(f"Cognito ClientError - Code: {error_code}, Message: {error_message}")
        raise HTTPException(status_code=500, detail=f"Error during signup: {error_message}")

    except Exception as e:
        # Catch any other unexpected exceptions and log details
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error during signup: {str(e)}")

def login_service(request: LoginRequest):
    try:
        # Authenticate user in Cognito
        response = cognito_client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': request.email_id, 'PASSWORD': request.password},
            ClientId=client_id
        )
        
        print(f"Cognito response: {response}")  # Log the full response
        
        # Check if AuthenticationResult exists
        if 'AuthenticationResult' not in response:
            raise HTTPException(status_code=500, detail="Failed to authenticate with Cognito")
        
        id_token = response['AuthenticationResult'].get('IdToken')
        access_token = response['AuthenticationResult'].get('AccessToken')
        
        if not id_token or not access_token:
            raise HTTPException(status_code=500, detail="Missing authentication tokens")

        # Check if the user exists in the local database
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email_id = %s", (request.email_id,))
                result = cursor.fetchone()
                if result:
                    return {
                        "statusCode": 200,
                        "message": "Login successful",
                        "user_id": result['user_id'],
                        "email_id": result['email_id'],
                        "name": result['name'],
                        "role": result['role'],
                        "id_token": id_token,
                        "access_token": access_token
                    }
                else:
                    return {"statusCode": 400, "message": "User not found in local database"}
        finally:
            connection.close()

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error'].get('Message', 'No detailed message')
        print(f"Cognito ClientError - Code: {error_code}, Message: {error_message}")
        
        if error_code == 'NotAuthorizedException':
            raise HTTPException(status_code=401, detail="Invalid email or password")
        else:
            raise HTTPException(status_code=500, detail=f"Error during authentication: {error_message}")

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error during authentication: {str(e)}")
