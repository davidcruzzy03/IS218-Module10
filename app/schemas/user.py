from datetime import datetime
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Validate information submitted when creating a user."""

    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_]+$",
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserRead(BaseModel):
    """Information that may safely be returned by the API."""

    id: uuid.UUID
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)