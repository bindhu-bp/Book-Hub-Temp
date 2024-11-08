from fastapi import APIRouter, Depends
from models.user_models import UserUpdateRequest, DeleteUser, EditProfileRequest
from config import get_current_user
from services.user_service import list_users_service, update_role_service, delete_user_service, get_contributed_books_service, get_borrowed_books_service, edit_user_profile_service

router = APIRouter()

# Route to list all users
@router.get("/list-users", response_model=dict)
async def list_users(current_user: dict = Depends(get_current_user)):
    return list_users_service()

# Route to update the role of a user
@router.post("/update-role", response_model=dict)
async def update_role(request: UserUpdateRequest, current_user: dict = Depends(get_current_user)):
    return update_role_service(request.email_id, request.role)

@router.delete("/delete-user")
async def delete_user(email_request: DeleteUser, current_user: dict = Depends(get_current_user)):
    return delete_user_service(email_request.email_id)


# Get all books contributed by the logged-in user
@router.get("/contributed_books")
async def get_contributed_books(current_user: dict = Depends(get_current_user)):
    user_id = current_user['user_id']
    return get_contributed_books_service(user_id)


# Get all books borrowed by the logged-in user
@router.get("/borrowed_books")
async def get_borrowed_books(current_user: dict = Depends(get_current_user)):
    user_id = current_user['user_id']
    return get_borrowed_books_service(user_id)


# Edit profile of the logged-in user (change name only)
@router.post("/edit_profile")
async def edit_profile(request: EditProfileRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user['user_id']
    return edit_user_profile_service(request, user_id)