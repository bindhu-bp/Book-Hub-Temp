from pydantic import BaseModel

class LoginRequest(BaseModel):
    email_id: str
    password: str

class SignupRequest(BaseModel):
    name: str
    email_id: str
    password: str

class CognitoEvent(BaseModel):
    request: dict
    context: dict

class ResetPasswordRequest(BaseModel):
    email_id: str  
    new_password: str
    confirm_password: str