from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from app.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.config import settings
from app.limiter import auth_limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or deleted")
    return user

@router.post("/register", response_model=UserResponse)
def register(user_in: UserRegister, request: Request, db: Session = Depends(get_db)):
    auth_limiter.check(request.client.host if request.client else "127.0.0.1")
    if settings.INVITE_ONLY:
        if user_in.invite_code != settings.REGISTRATION_INVITE_CODE:
            raise HTTPException(status_code=400, detail="Invalid invitation beta code.")

    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    user_count = db.query(User).count()
    is_first = (user_count == 0)

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_admin=is_first
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        is_admin=user.is_admin,
        storage_used_bytes=user.storage_used_bytes,
        has_assemblyai_key=bool(user.encrypted_assemblyai_key),
        has_llm_key=bool(user.encrypted_llm_key),
        created_at=user.created_at
    )

@router.post("/login", response_model=TokenResponse)
def login(user_in: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    auth_limiter.check(request.client.host if request.client else "127.0.0.1")
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token = create_access_token({"sub": user.id, "email": user.email, "admin": user.is_admin})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=not settings.DEBUG
    )
    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_admin=current_user.is_admin,
        storage_used_bytes=current_user.storage_used_bytes,
        has_assemblyai_key=bool(current_user.encrypted_assemblyai_key),
        has_llm_key=bool(current_user.encrypted_llm_key),
        created_at=current_user.created_at
    )
