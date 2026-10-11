from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Project, Job
from app.schemas import JobResponse
from app.routers.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.post("/render/{project_id}", response_model=JobResponse)
def trigger_render_job(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proj = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not proj.source_video_path:
        raise HTTPException(status_code=400, detail="Cannot render: Upload source video first.")

    active_jobs = db.query(Job).filter(
        Job.user_id == current_user.id,
        Job.status.in_(["QUEUED", "RUNNING"])
    ).count()
    if active_jobs >= settings.MAX_CONCURRENT_RENDERS_PER_USER:
        raise HTTPException(status_code=429, detail="You already have an active rendering job in progress.")

    job = Job(
        user_id=current_user.id,
        project_id=proj.id,
        job_type="full_render",
        status="QUEUED",
        stage="queued",
        progress=0
    )
    db.add(job)
    proj.status = "processing"
    db.commit()
    db.refresh(job)
    
    return job

@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in ["COMPLETED", "FAILED"]:
        return {"message": "Job has already ended."}
        
    job.status = "CANCELLED"
    job.stage = "cancelled_by_user"
    db.commit()
    return {"message": "Job cancellation requested."}
