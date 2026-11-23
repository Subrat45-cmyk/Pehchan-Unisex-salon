"""
Pehchan Unisex Salon & Beauty Parlour - Security & Authentication Utilities
Provides standard PBKDF2-HMAC-SHA256 password hashing and RFC 7519 HS256 JWT tokens
with zero external dependencies (standard library hashlib, hmac, secrets, json, base64).
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional, Dict, Any

# Default Secret Key - In production, load from environment variable PEHCHAN_SECRET_KEY
DEFAULT_SECRET_KEY = "pehchan-luxury-salon-ultra-secure-jwt-key-2026#supersecret"
ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 60 * 60 * 24  # 24 hours


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique 16-byte random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    )
    return f"pbkdf2:sha256:100000${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Safely verify a plain password against the stored PBKDF2 hash using constant-time comparison."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        algo_info, salt, stored_hash = parts
        _, hash_name, iterations_str = algo_info.split(":")
        iterations = int(iterations_str)

        computed = hashlib.pbkdf2_hmac(
            hash_name,
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=iterations,
        )
        return hmac.compare_digest(computed.hex(), stored_hash)
    except Exception:
        return False


def _b64_encode(data: bytes) -> str:
    """URL-safe base64 encoding without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64_decode(data: str) -> bytes:
    """URL-safe base64 decoding with restored padding."""
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(payload: Dict[str, Any], secret_key: str = DEFAULT_SECRET_KEY, expires_in: int = TOKEN_EXPIRY_SECONDS) -> str:
    """Create an RFC 7519 HMAC-SHA256 JWT."""
    header = {"alg": ALGORITHM, "typ": "JWT"}
    body = payload.copy()
    now = int(time.time())
    body["iat"] = now
    body["exp"] = now + expires_in

    header_b64 = _b64_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    message = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(secret_key.encode("utf-8"), message, hashlib.sha256).digest()
    sig_b64 = _b64_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_access_token(token: str, secret_key: str = DEFAULT_SECRET_KEY) -> Optional[Dict[str, Any]]:
    """Verify and decode an RFC 7519 HMAC-SHA256 JWT."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        message = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(secret_key.encode("utf-8"), message, hashlib.sha256).digest()
        actual_sig = _b64_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_bytes = _b64_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Check expiration
        exp = payload.get("exp")
        if exp and int(time.time()) > exp:
            return None

        return payload
    except Exception:
        return None
