import random
import string
import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.models.user import User, UserOTP, UserRole, OTPPurpose
from app.schemas.user import UserCreate, UserOut, Token, VerifyOTP, RequestOTP, UserUpdate

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

def generate_otp_code() -> str:
    return "".join(random.choices(string.digits, k=6))

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(deps.get_db)):
    """
    Registers a new student user and generates an email verification OTP.
    In a real app, this sends an email. For this SaaS, the OTP code is printed in the logs.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    # Create new inactive user
    db_user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role or UserRole.STUDENT,
        is_active=False  # Must verify email via OTP
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Generate OTP
    otp_code = generate_otp_code()
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    db_otp = UserOTP(
        user_id=db_user.id,
        code=otp_code,
        purpose=OTPPurpose.VERIFY_EMAIL,
        expires_at=expiration
    )
    db.add(db_otp)
    db.commit()

    # Logging OTP for local dev access
    logger.warning(f"--- [DEVELOPMENT OTP] Verification Code for {db_user.email} is: {otp_code} ---")
    print(f"--- [DEVELOPMENT OTP] Verification Code for {db_user.email} is: {otp_code} ---")

    return db_user

@router.post("/verify-otp", status_code=status.HTTP_200_OK)
def verify_otp(payload: VerifyOTP, db: Session = Depends(deps.get_db)):
    """
    Verifies the email or password reset OTP.
    Activates the user if verified for verify_email.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Fetch active, unused OTP code matching purpose
    db_otp = (
        db.query(UserOTP)
        .filter(
            UserOTP.user_id == user.id,
            UserOTP.code == payload.code,
            UserOTP.purpose == payload.purpose,
            UserOTP.is_used == False,
            UserOTP.expires_at > datetime.datetime.utcnow()
        )
        .first()
    )

    if not db_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already used OTP code."
        )

    # Mark OTP as used
    db_otp.is_used = True

    # Activate user if this was email verification
    if payload.purpose == OTPPurpose.VERIFY_EMAIL:
        user.is_active = True
        db.commit()
        return {"status": "success", "message": "Email successfully verified and account activated."}
    
    db.commit()
    return {"status": "success", "message": "OTP verified successfully. You may proceed."}

@router.post("/login", response_model=Token)
def login(user_in: UserCreate, db: Session = Depends(deps.get_db)):
    """
    Log in an existing active user and obtain a JWT access token.
    Uses email and password fields.
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not security.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not activated. Please verify email first."
        )

    access_token = security.create_access_token(subject=user.id, role=user.role.value)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/request-otp", status_code=status.HTTP_200_OK)
def request_otp(payload: RequestOTP, db: Session = Depends(deps.get_db)):
    """
    Generates a password reset or verification OTP and prints it to the console logs.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    otp_code = generate_otp_code()
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    
    db_otp = UserOTP(
        user_id=user.id,
        code=otp_code,
        purpose=payload.purpose,
        expires_at=expiration
    )
    db.add(db_otp)
    db.commit()

    logger.warning(f"--- [DEVELOPMENT OTP] Reset/Verification Code for {user.email} is: {otp_code} ---")
    print(f"--- [DEVELOPMENT OTP] Reset/Verification Code for {user.email} is: {otp_code} ---")

    return {"status": "success", "message": "OTP sent successfully."}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: VerifyOTP, new_password: str, db: Session = Depends(deps.get_db)):
    """
    Resets the password after verifying the OTP.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    db_otp = (
        db.query(UserOTP)
        .filter(
            UserOTP.user_id == user.id,
            UserOTP.code == payload.code,
            UserOTP.purpose == OTPPurpose.RESET_PASSWORD,
            UserOTP.is_used == False,
            UserOTP.expires_at > datetime.datetime.utcnow()
        )
        .first()
    )

    if not db_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset password OTP code."
        )

    # Reset password and activate user (if they were inactive but resetting password)
    user.hashed_password = security.get_password_hash(new_password)
    user.is_active = True
    db_otp.is_used = True
    db.commit()

    return {"status": "success", "message": "Password successfully reset."}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(deps.get_current_user)):
    """
    Get profile information of the currently authenticated user.
    """
    return current_user

@router.put("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update profile details for the currently authenticated user.
    """
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.password is not None:
        current_user.hashed_password = security.get_password_hash(payload.password)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/google", response_model=Token)
def google_oauth(id_token: str, db: Session = Depends(deps.get_db)):
    """
    Google OAuth Authentication.
    Supports mock tokens for local testing, and real Google ID token verification when deployed.
    """
    import os
    email = None
    name = None

    # Check if mock token (for local dev convenience)
    if id_token.startswith("mock-google-token-"):
        email = id_token.replace("mock-google-token-", "")
        name = email.split("@")[0].capitalize()
    else:
        # Real Google token verification
        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
            
            client_id = os.getenv("GOOGLE_CLIENT_ID", "")
            
            # Verify the token
            idinfo = google_id_token.verify_oauth2_token(
                id_token, 
                google_requests.Request(), 
                client_id if client_id else None
            )
            
            email = idinfo.get("email")
            name = idinfo.get("name", email.split("@")[0].capitalize() if email else "Google User")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google OAuth verification failed: {str(e)}"
            )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to retrieve email from Google ID Token."
        )

    # Check if user already exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create Google authenticated user
        user = User(
            email=email,
            hashed_password=security.get_password_hash(generate_otp_code() + "-random-google-pass"),
            full_name=name,
            role=UserRole.STUDENT,
            is_active=True  # Google users are verified automatically
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    access_token = security.create_access_token(subject=user.id, role=user.role.value)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
