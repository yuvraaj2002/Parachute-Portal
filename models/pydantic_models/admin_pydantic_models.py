from pydantic import BaseModel
from datetime import datetime
from typing import List

# User Management Models
class UserListResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

class UserDeactivateRequest(BaseModel):
    user_id: int

class UserDeactivateResponse(BaseModel):
    message: str
    user_id: int
    is_active: bool

class UserReactivateRequest(BaseModel):
    user_id: int

class UserReactivateResponse(BaseModel):
    message: str
    user_id: int
    is_active: bool

# Allowed Email Management Models
class AddAllowedEmailRequest(BaseModel):
    email: str

class AddAllowedEmailResponse(BaseModel):
    message: str
    email: str
    role: str
    id: int
