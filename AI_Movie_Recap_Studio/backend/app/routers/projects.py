import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Project, Scene
from app.schemas import ProjectCreate, ProjectResponse
from app.routers.auth import get_current_user
from app.config import settings
from app.services.video_engine import probe_media, extract_audio, detect_scenes_and_thumbnails

router = APIRouter(prefix="/api/projects", tags=["projects"])

def get_user_project_dir(user_id: str, project_id: str) -> str:
    path = os.path.join(settings.STORAGE_DIR, "users", user_id, "projects", project_id)
    os.makedirs(path, exist_ok=True)
    return path

@router.post("/", response_model=ProjectResponse)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proj = Project(
        user_id=current_user.id,
        title=project_in.title,
        target_language=project_in.target_language,
        aspect_ratio=project_in.aspect_ratio,
        target_duration_minutes=project_in.target_duration_minutes,
        burn_subtitles=project_in.burn_subtitles,
        voice_name=project_in.voice_name
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    get_user_project_dir(current_user.id, proj.id)
    
    return ProjectResponse(
        id=proj.id,
        title=proj.title,
        target_language=proj.target_language,
        aspect_ratio=proj.aspect_ratio,
        target_duration_minutes=project_in.target_duration_minutes,
        burn_subtitles=proj.burn_subtitles,
        voice_name=proj.voice_name,
        source_duration=proj.source_duration,
        status=proj.status,
        transcript_text=proj.transcript_text,
        script_text=proj.script_text,
        has_video=bool(proj.source_video_path),
        has_render=bool(proj.rendered_video_path),
        created_at=proj.created_at,
        updated_at=proj.updated_at
    )

@router.get("/", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at.desc()).all()
    return [
        ProjectResponse(
            id=p.id,
            title=p.title,
            target_language=p.target_language,
            aspect_ratio=p.aspect_ratio,
            target_duration_minutes=p.target_duration_minutes,
            burn_subtitles=p.burn_subtitles,
            voice_name=p.voice_name,
            source_duration=p.source_duration,
            status=p.status,
            transcript_text=p.transcript_text,
            script_text=p.script_text,
            has_video=bool(p.source_video_path),
            has_render=bool(p.rendered_video_path),
            created_at=p.created_at,
            updated_at=p.updated_at
        ) for p in projects
    ]

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=proj.id,
        title=proj.title,
        target_language=proj.target_language,
        aspect_ratio=proj.aspect_ratio,
        target_duration_minutes=proj.target_duration_minutes,
        burn_subtitles=proj.burn_subtitles,
        voice_name=proj.voice_name,
        source_duration=proj.source_duration,
        status=proj.status,
        transcript_text=proj.transcript_text,
        script_text=proj.script_text,
        has_video=bool(proj.source_video_path),
        has_render=bool(proj.rendered_video_path),
        created_at=proj.created_at,
        updated_at=proj.updated_at
    )

@router.post("/{project_id}/upload-video")
async def upload_video(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    p_dir = get_user_project_dir(current_user.id, proj.id)
    safe_filename = f"source_{uuid.uuid4().hex[:8]}.mp4"
    dest_path = os.path.join(p_dir, safe_filename)

    total_bytes = 0
    with open(dest_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            total_bytes += len(chunk)
            if total_bytes > settings.MAX_UPLOAD_BYTES:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                raise HTTPException(status_code=413, detail=f"File exceeds maximum size limit.")
            buffer.write(chunk)

    if current_user.storage_used_bytes + total_bytes > settings.MAX_STORAGE_PER_USER_BYTES:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=400, detail="User storage quota exceeded.")

    try:
        media_info = probe_media(dest_path)
    except Exception as e:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=400, detail=f"Invalid or corrupted video: {str(e)}")

    if media_info["duration"] > settings.MAX_SOURCE_DURATION_SEC:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=400, detail=f"Duration exceeds limits.")

    proj.source_video_path = dest_path
    proj.source_duration = media_info["duration"]
    proj.source_width = media_info["width"]
    proj.source_height = media_info["height"]
    proj.status = "video_uploaded"
    
    current_user.storage_used_bytes += total_bytes
    db.commit()

    audio_path = os.path.join(p_dir, "audio.wav")
    try:
        extract_audio(dest_path, audio_path)
        proj.source_audio_path = audio_path
        
        thumb_dir = os.path.join(p_dir, "thumbnails")
        scenes = detect_scenes_and_thumbnails(dest_path, thumb_dir)
        for s in scenes:
            db.add(Scene(
                project_id=proj.id,
                scene_index=s["index"],
                start_time=s["start"],
                end_time=s["end"],
                thumbnail_path=s["thumbnail"]
            ))
        db.commit()
    except Exception as e:
        pass

    return {"message": "Video uploaded and verified successfully."}

@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    p_dir = os.path.join(settings.STORAGE_DIR, "users", current_user.id, "projects", proj.id)
    if os.path.exists(p_dir):
        shutil.rmtree(p_dir, ignore_errors=True)

    db.delete(proj)
    db.commit()
    return {"message": "Project deleted successfully."}
