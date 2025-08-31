from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .config import settings
from .database import SessionLocal
from .models import User
from sqlalchemy import select, or_, func

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# для эндпоинтов где токен обязателен (например /users/me)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# для эндпоинтов где токен может быть (например /feed/public)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(tz=timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.scalars(select(User).where(User.username == username)).first()

def get_user_by_login(db: Session, login: str) -> Optional[User]:
    login = login.strip()
    return db.scalars(
        select(User).where(
            or_(
                User.username == login,
                func.lower(User.email) == login.lower()
            )
        )
    ).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_login(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user

def get_current_user_optional(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme_optional)
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if not username:
            return None
    except JWTError:
        return None
    return get_user_by_username(db, username)
