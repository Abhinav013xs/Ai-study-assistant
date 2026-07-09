from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: Optional[UserRole] = UserRole.STUDENT

# Properties to receive on user creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

# Properties to receive on user update
class UserUpdate(BaseModel):
    password: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

# Properties to return to client (Database representations)
class UserOut(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[int] = None
    role: Optional[str] = None

# OTP validation schema
class VerifyOTP(BaseModel):
    email: EmailStr
    code: str
    purpose: str

class RequestOTP(BaseModel):
    email: EmailStr
    purpose: str
