from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: str | None = None

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    email: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=280)

class UserPublic(BaseModel):
    id: int
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    followers_count: int
    following_count: int
    posts_count: int
    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    text: str = Field(min_length=1, max_length=280)

class PostUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=280)

class PostPublic(BaseModel):
    id: int
    author: UserPublic
    text: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    edited: bool
    original_post_id: Optional[int] = None
    likes_count: int
    reposts_count: int
    liked_by_me: bool = False
    reposted_by_me: bool = False
    hashtags: List[str] = []
    class Config:
        from_attributes = True

class FeedResponse(BaseModel):
    items: List[PostPublic]
    next_offset: int | None = None
