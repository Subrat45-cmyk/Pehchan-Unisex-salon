"""
Pehchan Unisex Salon & Beauty Parlour - Authentication Router
"""

from fastapi import APIRouter, HTTPException, Depends, Header, status
from typing import Optional
from backend.app.models.schemas import LoginRequest, TokenResponse
from backend.app.db.connection import get_db_connection
from backend.app.utils.security import verify_password, create_access_token, verify_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def get_current_admin(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency to validate Bearer JWT token on protected admin endpoints."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header with Bearer token is required"
        )
    token = authorization.split(" ")[1]
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token"
        )

    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT id, full_name, email, role, is_active FROM admin_users WHERE id = ?",
            (payload.get("sub"),)
        ).fetchone()

        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account does not exist or has been deactivated"
            )
        return dict(user)
    finally:
        conn.close()


@router.post("/login", response_model=TokenResponse)
def login(creds: LoginRequest):
    """Authenticate salon owner or manager and generate JWT."""
    conn = get_db_connection()
    try:
        user = conn.execute(
            "SELECT id, full_name, email, password_hash, role, is_active FROM admin_users WHERE email = ?",
            (creds.email.lower().strip(),)
        ).fetchone()

        if not user or not verify_password(creds.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )

        token = create_access_token({
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"],
            "name": user["full_name"]
        })

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 86400,
            "admin": {
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"]
            }
        }
    finally:
        conn.close()


@router.get("/me")
def get_profile(admin: dict = Depends(get_current_admin)):
    """Return verified admin user details."""
    return {"status": "success", "admin": admin}
