import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings


def get_encryption_key_bytes() -> bytes:
    """Derives a 32-byte key from the configured ENCRYPTION_KEY setting."""
    raw_key = settings.ENCRYPTION_KEY.encode("utf-8")
    if len(raw_key) < 32:
        # Pad to 32 bytes
        return raw_key.ljust(32, b"0")
    return raw_key[:32]


def encrypt_secret(plain_text: str) -> str:
    """
    Encrypts sensitive text using AES-256-GCM.
    Returns base64-encoded string: nonce (12 bytes) + ciphertext + tag (16 bytes).
    """
    if not plain_text:
        return ""
    key = get_encryption_key_bytes()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt_secret(encrypted_base64: str) -> str:
    """Decrypts base64-encoded AES-256-GCM payload."""
    if not encrypted_base64:
        return ""
    try:
        raw_bytes = base64.b64decode(encrypted_base64.encode("utf-8"))
        if len(raw_bytes) < 28:
            raise ValueError("Invalid encrypted secret length.")
        nonce = raw_bytes[:12]
        ciphertext = raw_bytes[12:]
        key = get_encryption_key_bytes()
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decrypt secret: {str(e)}")
