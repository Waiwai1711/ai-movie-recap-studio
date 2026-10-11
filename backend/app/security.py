import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

def get_aesgcm_cipher() -> AESGCM:
    key_bytes = bytes.fromhex(settings.ENCRYPTION_SECRET_KEY)
    if len(key_bytes) != 32:
        raise ValueError("ENCRYPTION_SECRET_KEY must be a 64-character hex string (32 bytes).")
    return AESGCM(key_bytes)

def encrypt_api_key(plain_key: str) -> str:
    if not plain_key:
        return ""
    cipher = get_aesgcm_cipher()
    nonce = os.urandom(12)
    ciphertext = cipher.encrypt(nonce, plain_key.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")

def decrypt_api_key(encrypted_token: str) -> str:
    if not encrypted_token:
        return ""
    cipher = get_aesgcm_cipher()
    raw = base64.b64decode(encrypted_token.encode("utf-8"))
    nonce = raw[:12]
    ciphertext = raw[12:]
    return cipher.decrypt(nonce, ciphertext, None).decode("utf-8")

def mask_api_key(key: Optional[str]) -> str:
    if not key:
        return "Not Set"
    if len(key) <= 8:
        return "********"
    return f"{key[:4]}...{key[-4:]}"
