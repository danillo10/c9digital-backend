from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models.client import ClientStatus


class ClientBase(BaseModel):
    name: str
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    monthly_budget: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ClientStatus] = None
    monthly_budget: Optional[str] = None
    logo_url: Optional[str] = None


class ClientResponse(ClientBase):
    id: int
    owner_id: int
    logo_url: Optional[str] = None
    status: ClientStatus
    created_at: datetime

    class Config:
        from_attributes = True
