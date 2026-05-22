from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.campaign import CampaignType, CampaignStatus, TaskStatus, TaskPriority


class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: CampaignType
    budget: Optional[float] = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    goals: Optional[Dict[str, Any]] = {}


class CampaignCreate(CampaignBase):
    client_id: int


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    budget: Optional[float] = None
    spent: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    goals: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None


class CampaignResponse(CampaignBase):
    id: int
    client_id: int
    status: CampaignStatus
    spent: float
    metrics: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    client_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None


class TaskCommentCreate(BaseModel):
    content: str


class TaskCommentResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    content: str
    is_activity: bool
    activity_type: Optional[str] = None
    created_at: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class TaskResponse(TaskBase):
    id: int
    client_id: int
    status: TaskStatus
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskDetailResponse(TaskResponse):
    comments: List[TaskCommentResponse] = []

    class Config:
        from_attributes = True
