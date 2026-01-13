from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.models import User, Settings
from app.auth import (
    verify_password, get_password_hash, create_access_token,
    generate_totp_secret, get_totp_uri, generate_qr_code, verify_totp,
    get_current_user
)
from app.config import settings as app_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class SetupMFAResponse(BaseModel):
    qr_code: str
    secret: str

class VerifyMFARequest(BaseModel):
    code: str

@router.post("/login")
async def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check MFA if enabled
    if user.mfa_enabled:
        if not request.totp_code:
            return JSONResponse(
                status_code=200,
                content={"mfa_required": True, "message": "MFA code required"}
            )
        
        if not verify_totp(user.totp_secret, request.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )
    
    token = create_access_token(data={"sub": user.username})
    
    response = JSONResponse(content={
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "mfa_enabled": user.mfa_enabled
    })
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,
        samesite="lax"
    )
    return response

@router.post("/logout")
async def logout(response: Response):
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie("access_token")
    return response

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "username": user.username,
        "mfa_enabled": user.mfa_enabled,
        "created_at": user.created_at.isoformat()
    }

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    user.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/setup-mfa", response_model=SetupMFAResponse)
async def setup_mfa(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    secret = generate_totp_secret()
    uri = get_totp_uri(secret, user.username)
    qr_code = generate_qr_code(uri)
    
    # Store secret temporarily (not enabled yet)
    user.totp_secret = secret
    db.commit()
    
    return {"qr_code": qr_code, "secret": secret}

@router.post("/verify-mfa")
async def verify_mfa(
    request: VerifyMFARequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not set up. Call /setup-mfa first"
        )
    
    if not verify_totp(user.totp_secret, request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code"
        )
    
    user.mfa_enabled = True
    db.commit()
    
    return {"message": "MFA enabled successfully"}

@router.post("/disable-mfa")
async def disable_mfa(
    request: VerifyMFARequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled"
        )
    
    if not verify_totp(user.totp_secret, request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code"
        )
    
    user.mfa_enabled = False
    user.totp_secret = None
    db.commit()
    
    return {"message": "MFA disabled successfully"}
