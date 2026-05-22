from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.support import TicketStatus, TicketPriority, TicketCategory, MessageSender


class TicketMessageBase(BaseModel):
    content: str


class TicketMessageCreate(TicketMessageBase):
    pass


class TicketMessageResponse(TicketMessageBase):
    id: int
    ticket_id: int
    sender: MessageSender
    is_internal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TicketBase(BaseModel):
    title: str
    description: str
    priority: Optional[TicketPriority] = TicketPriority.MEDIUM
    category: Optional[TicketCategory] = TicketCategory.OTHER


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None


class TicketListResponse(TicketBase):
    id: int
    user_id: int
    ticket_number: str
    status: TicketStatus
    is_read_by_user: bool
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketDetailResponse(TicketListResponse):
    messages: List[TicketMessageResponse] = []
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
