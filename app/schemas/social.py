from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.social import SocialPlatform, PostStatus


class SocialAccountBase(BaseModel):
    platform: SocialPlatform
    username: Optional[str] = None
    account_name: Optional[str] = None
    profile_url: Optional[str] = None


class SocialAccountCreate(SocialAccountBase):
    client_id: int
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    posts_count: Optional[int] = 0


class SocialAccountUpdate(BaseModel):
    username: Optional[str] = None
    account_name: Optional[str] = None
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    posts_count: Optional[int] = None
    is_connected: Optional[bool] = None


class SocialAccountResponse(SocialAccountBase):
    id: int
    client_id: int
    followers_count: int
    following_count: int
    posts_count: int
    is_connected: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SocialPostBase(BaseModel):
    title: Optional[str] = None
    content: str
    media_urls: Optional[List[str]] = []
    hashtags: Optional[List[str]] = []
    scheduled_at: Optional[datetime] = None


class SocialPostCreate(SocialPostBase):
    account_id: int


class SocialPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    media_urls: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None
    status: Optional[PostStatus] = None
    scheduled_at: Optional[datetime] = None


class SocialPostResponse(SocialPostBase):
    id: int
    account_id: int
    status: PostStatus
    likes_count: int
    comments_count: int
    shares_count: int
    reach: int
    published_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
