from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class OrgCreate(BaseModel):
    name: Optional[str] = None


class OrgSettings(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    brand_primary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    brand_secondary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class InviteRequest(BaseModel):
    email: EmailStr


class OrgUserResponse(BaseModel):
    id: UUID
    email: str
    company_name: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OrgResponse(BaseModel):
    id: UUID
    name: str
    contact_email: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    brand_primary_color: str
    brand_secondary_color: str
    has_logo: bool
    subscription_plan: str
    subscription_status: str
    audits_this_month: int
    audits_limit: int
    created_at: Optional[datetime] = None
    users_count: int

    model_config = {"from_attributes": True}
