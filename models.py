from pydantic import BaseModel
from datetime import date   
from typing import List

# Pydantic models for request data
class LoginRequest(BaseModel):
    email_id: str
    password: str

class SignupRequest(BaseModel):
    name: str
    email_id: str
    password: str

class Book(BaseModel):
    book_name: str
    author: str
    contributors: str
    copies: int

class Collection(BaseModel):
    collection_name: str

class Resource(BaseModel):
    resource_name: str
    link:str
    description:str
    collection_name:str

class BorrowRequest(BaseModel):
    book_name: str
    borrower: str

class ReturnRequest(BaseModel):
    book_name: str
    borrower: str

class CollectionDisplay(BaseModel):
    collection_name: str

class ResourceDisaplay(BaseModel):
    resource_name: str
    link: str

class ResetPasswordRequest(BaseModel):
    email_id: str
    new_password: str

class UserUpdateRequest(BaseModel):
    email_id: str
    role: str

class CognitoEvent(BaseModel):
    request: dict
    context: dict

class SubscriptionRequest(BaseModel):
    email: str

class UploadPayload(BaseModel):
    user_id: str
    filename: str