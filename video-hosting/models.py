from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    email: str
    username: str
    password: str

class Video(BaseModel):
    title: str
    description: Optional[str] = None
    url: str
    user_id: str
    created_at: Optional[datetime] = None

class Comment(BaseModel):
    content: str
    user_id: str
    video_id: str
    created_at: Optional[datetime] = None

class Complaint(BaseModel):
    reason: str
    user_id: str
    video_id: str