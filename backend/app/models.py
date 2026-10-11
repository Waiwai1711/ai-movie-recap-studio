import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def gen_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    storage_used_bytes = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    encrypted_assemblyai_key = Column(Text, nullable=True)
    encrypted_llm_key = Column(Text, nullable=True)

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    target_language = Column(String(10), default="my")
    aspect_ratio = Column(String(10), default="16:9")
    target_duration_minutes = Column(Integer, default=3)
    burn_subtitles = Column(Boolean, default=True)
    voice_name = Column(String(50), default="my-MM-ThihaNeural")
    
    source_video_path = Column(String(512), nullable=True)
    source_audio_path = Column(String(512), nullable=True)
    source_duration = Column(Float, default=0.0)
    source_width = Column(Integer, default=0)
    source_height = Column(Integer, default=0)
    
    transcript_text = Column(Text, nullable=True)
    script_text = Column(Text, nullable=True)
    subtitles_srt = Column(Text, nullable=True)
    rendered_video_path = Column(String(512), nullable=True)
    status = Column(String(50), default="created")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="projects")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan")

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    scene_index = Column(Integer, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    thumbnail_path = Column(String(512), nullable=True)
    selected = Column(Boolean, default=True)

    project = relationship("Project", back_populates="scenes")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(String(50), default="full_render")
    status = Column(String(20), default="QUEUED", index=True)
    stage = Column(String(50), default="initializing")
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="jobs")
    project = relationship("Project", back_populates="jobs")
