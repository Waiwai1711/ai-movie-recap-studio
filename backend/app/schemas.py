from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    invite_code: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    is_admin: bool
    storage_used_bytes: int
    has_assemblyai_key: bool
    has_llm_key: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ProjectCreate(BaseModel):
    title: str
    target_language: str = "my"
    aspect_ratio: str = "16:9"
    target_duration_minutes: int = 3
    burn_subtitles: bool = True
    voice_name: str = "my-MM-ThihaNeural"

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    target_language: Optional[str] = None
    aspect_ratio: Optional[str] = None
    target_duration_minutes: Optional[int] = None
    burn_subtitles: Optional[bool] = None
    voice_name: Optional[str] = None
    transcript_text: Optional[str] = None
    script_text: Optional[str] = None
    subtitles_srt: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    title: str
    target_language: str
    aspect_ratio: str
    target_duration_minutes: int
    burn_subtitles: bool
    voice_name: str
    source_duration: float
    status: str
    transcript_text: Optional[str] = None
    script_text: Optional[str] = None
    has_video: bool
    has_render: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class KeyUpdate(BaseModel):
    assemblyai_key: Optional[str] = None
    llm_key: Optional[str] = None

class JobResponse(BaseModel):
    id: str
    project_id: str
    job_type: str
    status: str
    stage: str
    progress: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
