import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import KeyUpdate
from app.security import encrypt_api_key, decrypt_api_key, mask_api_key
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/keys")
def get_key_statuses(current_user: User = Depends(get_current_user)):
    aai_key = decrypt_api_key(current_user.encrypted_assemblyai_key) if current_user.encrypted_assemblyai_key else None
    llm_key = decrypt_api_key(current_user.encrypted_llm_key) if current_user.encrypted_llm_key else None
    
    return {
        "assemblyai_configured": bool(aai_key),
        "assemblyai_masked": mask_api_key(aai_key),
        "llm_configured": bool(llm_key),
        "llm_masked": mask_api_key(llm_key)
    }

@router.post("/keys")
def update_keys(keys_in: KeyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if keys_in.assemblyai_key is not None:
        if keys_in.assemblyai_key.strip() == "":
            current_user.encrypted_assemblyai_key = None
        else:
            current_user.encrypted_assemblyai_key = encrypt_api_key(keys_in.assemblyai_key.strip())
            
    if keys_in.llm_key is not None:
        if keys_in.llm_key.strip() == "":
            current_user.encrypted_llm_key = None
        else:
            current_user.encrypted_llm_key = encrypt_api_key(keys_in.llm_key.strip())

    db.commit()
    return {"message": "Keys securely updated and encrypted at rest."}

@router.post("/test-assemblyai")
async def test_assemblyai_key(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.encrypted_assemblyai_key:
        raise HTTPException(status_code=400, detail="No AssemblyAI key configured.")
    raw_key = decrypt_api_key(current_user.encrypted_assemblyai_key)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.get(
                "https://api.assemblyai.com/v2/account",
                headers={"Authorization": raw_key}
            )
            if r.status_code == 200:
                return {"valid": True, "message": "AssemblyAI API key connected successfully."}
            else:
                return {"valid": False, "status_code": r.status_code, "error": r.text}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to communicate with AssemblyAI: {str(e)}")
