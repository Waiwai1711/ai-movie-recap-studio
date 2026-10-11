import pytest
from app.security import encrypt_api_key, decrypt_api_key, mask_api_key

def test_byok_encryption_cycle():
    raw_key = "aai_live_89342784918237491823749"
    encrypted = encrypt_api_key(raw_key)
    assert encrypted != raw_key
    assert len(encrypted) > 20
    decrypted = decrypt_api_key(encrypted)
    assert decrypted == raw_key

def test_mask_api_key():
    key = "1234567890abcdef"
    masked = mask_api_key(key)
    assert masked == "1234...cdef"
