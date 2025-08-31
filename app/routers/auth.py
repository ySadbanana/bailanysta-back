from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .. import schemas
from ..auth import authenticate_user, create_access_token, get_password_hash, get_db
from ..models import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=schemas.UserPublic, status_code=201)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    email_norm = (payload.email or None)
    if email_norm:
        email_norm = email_norm.strip().lower()
    if email_norm and db.scalar(select(User).where(func.lower(User.email) == email_norm)):
        raise HTTPException(status_code=400, detail="Email already in use")
    existing = db.scalar(select(User).where(User.username == payload.username))
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    if payload.email and db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=400, detail="Email already in use")
    user = User(
        username=payload.username,
        email=email_norm,
        display_name=payload.display_name,
        bio=payload.bio,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.UserPublic(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        bio=user.bio,
        followers_count=0, following_count=0, posts_count=0,
    )

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = create_access_token(subject=user.username, expires_delta=timedelta(minutes=60))
    return schemas.Token(access_token=token)
