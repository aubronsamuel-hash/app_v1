from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime

class UserIn(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool


class UserAdminUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("role")
    @classmethod
    def _valid_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"admin", "intermittent"}:
            raise ValueError("invalid role")
        return v

class TokenOut(BaseModel):
    access_token: str


class NotificationPrefsIn(BaseModel):
    email: Optional[str] = None
    telegram: Optional[bool] = None
    telegram_chat_id: Optional[str] = None


class PositionIn(BaseModel):
    label: str
    count: int = Field(ge=1)
    skills: Dict[str, str] = {}


class MissionBase(BaseModel):
    title: str
    start: datetime
    end: datetime
    location: Optional[str] = None
    status: str = Field(default="draft")

    @field_validator("status")
    @classmethod
    def _valid_status(cls, v: str) -> str:
        if v not in ("draft", "published"):
            raise ValueError("invalid status")
        return v

    @field_validator("end")
    @classmethod
    def _end_after_start(cls, v: datetime, info):
        start = info.data.get("start")
        if start is not None and v <= start:
            raise ValueError("end must be after start")
        return v


class MissionCreate(MissionBase):
    positions: List[PositionIn] = []


class MissionUpdate(BaseModel):
    title: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    location: Optional[str] = None
    status: Optional[str] = None
    positions: Optional[List[PositionIn]] = None

    @field_validator("status")
    @classmethod
    def _valid_status_u(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("draft", "published"):
            raise ValueError("invalid status")
        return v

    @field_validator("end")
    @classmethod
    def _end_after_start_u(cls, v: Optional[datetime], info):
        start = info.data.get("start")
        # If only end is provided, cannot validate here; router will re-validate combined
        return v


class MissionOut(MissionBase):
    id: int
    positions: List[PositionIn] = []


class AssignmentIn(BaseModel):
    role_label: str
    user_id: int
    status: str = "invited"

    @field_validator("status")
    @classmethod
    def _valid_status_a(cls, v: str) -> str:
        allowed = {"invited", "confirmed", "declined", "tentative"}
        if v not in allowed:
            raise ValueError("invalid status")
        return v


class AssignmentOut(BaseModel):
    id: int
    mission_id: int
    user_id: int
    role_label: str
    status: str

    @field_validator("status")
    @classmethod
    def _valid_status_o(cls, v: str) -> str:
        allowed = {"invited", "confirmed", "declined", "tentative"}
        if v not in allowed:
            raise ValueError("invalid status")
        return v
