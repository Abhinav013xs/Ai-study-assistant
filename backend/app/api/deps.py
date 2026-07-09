from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.config import settings
from app.core.security import verify_access_token
from app.models.user import User, UserRole

# Reusable database session dependency
def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# Token extractor using standard Authorization: Bearer <token> header
security_scheme = HTTPBearer()

def get_current_user(
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> User:
    """
    Decodes JWT, validates existence, and returns the current user model.
    Throws HTTP 401/403 exceptions on validation failure.
    """
    payload = verify_access_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user profile",
        )
    
    return user

def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Validates that the current user has the ADMIN role.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required.",
        )
    return current_user
