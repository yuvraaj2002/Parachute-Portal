from pydantic import BaseModel, EmailStr, field_validator, Field, ConfigDict
from typing import Optional, Dict, List, Any
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model for API responses"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

class UserBase(BaseModel):
    first_name: str
    last_name: str
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    @field_validator('username')
    @classmethod
    def get_display_username(cls, v, info):
        if hasattr(info.data.get('__object__'), 'display_username'):
            return info.data.get('__object__').display_username
        return v

    model_config = ConfigDict(from_attributes=True)

class SignupResponse(BaseModel):    
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
