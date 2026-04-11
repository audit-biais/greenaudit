from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# --- Request schemas ---

class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(min_length=1, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# --- Response schemas ---

class OrgInfo(BaseModel):
    id: UUID
    name: str
    has_logo: bool = False
    brand_primary_color: str = "#1B5E20"
    brand_secondary_color: str = "#2E7D32"
    subscription_plan: str = "starter"
    subscription_status: str = "inactive"
    audits_this_month: int = 0
    audits_limit: int = 1

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: UUID
    email: str
    company_name: str
    role: str = "member"
    subscription_plan: str
    subscription_status: str
    audits_this_month: int
    audits_limit: int
    organization: Optional[OrgInfo] = None
    is_superadmin: bool = False

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
