from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MonitoringConfigCreate(BaseModel):
    frequency_days: int = Field(default=7, ge=1, le=365)


class MonitoringAlertResponse(BaseModel):
    id: UUID
    monitoring_config_id: UUID
    claim_text: str
    source_url: Optional[str] = None
    is_read: bool
    detected_at: datetime

    model_config = {"from_attributes": True}


class MonitoringConfigResponse(BaseModel):
    id: UUID
    audit_id: UUID
    is_active: bool
    frequency_days: int
    last_checked_at: Optional[datetime] = None
    next_check_at: Optional[datetime] = None
    created_at: datetime
    unread_alerts_count: int = 0
    alerts: List[MonitoringAlertResponse] = []

    model_config = {"from_attributes": True}
