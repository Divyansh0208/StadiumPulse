"""Real staff auth: hashed passwords, DB-backed users. Replaces the hardcoded
staff/demo credential from the prototype.
"""
from datetime import datetime, timedelta, UTC

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.shared.config import get_settings
from backend.shared.models import StaffUser

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_staff(db: Session, username: str, password: str) -> StaffUser | None:
    user = db.query(StaffUser).filter(StaffUser.username == username, StaffUser.active.is_(True)).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_staff(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    try:
        payload = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload["sub"]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid or expired token")
