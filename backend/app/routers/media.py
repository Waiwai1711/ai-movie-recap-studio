import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Project
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/media", tags=["media"])

@router.get("/download/{project_id}/video")
def download_rendered_video(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not proj or not proj.rendered_video_path or not os.path.exists(proj.rendered_video_path):
        raise HTTPException(status_code=404, detail="Rendered video not found or not finished.")

    return FileResponse(
        path=proj.rendered_video_path,
        media_type="video/mp4",
        filename=f"{proj.title.replace(' ', '_')}_recap.mp4"
    )

@router.get("/download/{project_id}/subtitles")
def download_subtitles(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not proj or not proj.subtitles_srt:
        raise HTTPException(status_code=404, detail="Subtitles not generated.")

    srt_path = os.path.join(os.path.dirname(proj.source_video_path), "subtitles.srt")
    return FileResponse(
        path=srt_path,
        media_type="text/plain",
        filename=f"{proj.title.replace(' ', '_')}.srt"
    )
