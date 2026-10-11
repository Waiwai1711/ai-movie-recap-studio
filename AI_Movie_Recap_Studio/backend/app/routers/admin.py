import psutil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Project, Job
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])

def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required.")
    return current_user

@router.get("/system-stats")
def get_system_stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    cpu_usage = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    total_users = db.query(User).count()
    total_projects = db.query(Project).count()
    active_jobs = db.query(Job).filter(Job.status.in_(["QUEUED", "RUNNING"])).count()
    failed_jobs = db.query(Job).filter(Job.status == "FAILED").count()
    
    return {
        "cpu_percent": cpu_usage,
        "ram_used_percent": mem.percent,
        "ram_free_mb": mem.available // (1024 * 1024),
        "disk_free_gb": disk.free // (1024 * 1024 * 1024),
        "total_users": total_users,
        "total_projects": total_projects,
        "active_jobs": active_jobs,
        "failed_jobs": failed_jobs
    }
