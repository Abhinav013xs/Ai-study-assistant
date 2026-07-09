import datetime
from typing import Optional, Union, Any
from jose import jwt
import bcrypt
from app.core.config import settings

def get_password_hash(password: str) -> str:
    """
    Generate a bcrypt hash of the input password.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its bcrypt hash.
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False

def create_access_token(
    subject: Union[str, Any], role: str, expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """
    Generate a signed JWT access token.
    """
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def verify_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify the token. Returns claims dict if valid, else None.
    """
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return decoded_token
    except jwt.JWTError:
        return None
