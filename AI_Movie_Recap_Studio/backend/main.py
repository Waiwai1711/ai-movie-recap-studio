from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import engine, Base
from app.routers import auth, projects, jobs, media, settings as settings_router, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def maintenance_check(request: Request, call_next):
    if settings.MAINTENANCE_MODE and not request.url.path.startswith("/api/admin"):
        return JSONResponse(
            status_code=503,
            content={"detail": "System is under scheduled maintenance."}
        )
    return await call_next(request)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(jobs.router)
app.include_router(media.router)
app.include_router(settings_router.router)
app.include_router(admin.router)

@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}
