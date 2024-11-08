from pydantic import BaseModel

class UserUpdateRequest(BaseModel):
    email_id: str
    role: str

class DeleteUser(BaseModel):
    email_id: str

class EditProfileRequest(BaseModel):
    new_name: str