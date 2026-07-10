import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    permissions: list[str] | dict[str, Any] = []

    model_config = {
        "from_attributes": True
    }


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)
    timezone: str = Field(default="UTC", max_length=50)
    language: str = Field(default="en", max_length=10)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format.")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not USERNAME_REGEX.match(v):
            raise ValueError("Username can only contain alphanumeric characters, underscores, and hyphens.")
        return v


class UserLogin(BaseModel):
    username_or_email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    username: str
    email: str
    avatar_url: str | None = None
    timezone: str
    language: str
    is_active: bool
    is_verified: bool
    role: RoleResponse
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None

    model_config = {
        "from_attributes": True
    }


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=500)
    timezone: str | None = Field(default=None, max_length=50)
    language: str | None = Field(default=None, max_length=10)


class MessageResponse(BaseModel):
    success: bool
    message: str
