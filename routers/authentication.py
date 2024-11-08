from fastapi import APIRouter, HTTPException, Depends
from models.auth_models import LoginRequest, SignupRequest, CognitoEvent, ResetPasswordRequest
from services.auth_service import login_service, signup_service, lambda_handler_service, reset_password

router = APIRouter()

@router.post("/test_users")
async def lambda_handler(event: CognitoEvent):
    return lambda_handler_service(event)

@router.post("/login")
async def login(request: LoginRequest):
    return login_service(request)

@router.post("/signup")
async def signup(request: SignupRequest):
    return signup_service(request)

@router.post("/reset-password")
async def reset_password_route(request: ResetPasswordRequest):
    return reset_password(request)