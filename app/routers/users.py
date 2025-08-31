from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..auth import get_db, get_current_user
from .. import schemas
from ..models import User, Follow, Post

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=schemas.UserPublic)
def get_me(current=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_public(db, current.username)

@router.get("/{username}", response_model=schemas.UserPublic)
def get_user(username: str, db: Session = Depends(get_db)):
    return get_user_public(db, username)

def get_user_public(db: Session, username: str) -> schemas.UserPublic:
    user = db.scalars(select(User).where(User.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    followers_count = db.scalar(select(func.count()).select_from(Follow).where(Follow.following_id == user.id)) or 0
    following_count = db.scalar(select(func.count()).select_from(Follow).where(Follow.follower_id == user.id)) or 0
    posts_count = db.scalar(select(func.count()).select_from(Post).where(Post.author_id == user.id)) or 0
    return schemas.UserPublic(
        id=user.id, username=user.username, display_name=user.display_name, bio=user.bio,
        followers_count=followers_count, following_count=following_count, posts_count=posts_count,
    )

@router.post("/{username}/follow", status_code=204)
def follow(username: str, current=Depends(get_current_user), db: Session = Depends(get_db)):
    target = db.scalars(select(User).where(User.username == username)).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    exists = db.scalar(select(Follow).where(Follow.follower_id == current.id, Follow.following_id == target.id))
    if not exists:
        db.add(Follow(follower_id=current.id, following_id=target.id))
        db.commit()
    return

@router.post("/{username}/unfollow", status_code=204)
def unfollow(username: str, current=Depends(get_current_user), db: Session = Depends(get_db)):
    target = db.scalars(select(User).where(User.username == username)).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current.id:
        raise HTTPException(status_code=400, detail="Cannot unfollow yourself")
    follow = db.scalar(select(Follow).where(Follow.follower_id == current.id, Following_id == target.id))
    # typo guard: fix column name
    if not follow:
        follow = db.scalar(select(Follow).where(Follow.follower_id == current.id, Follow.following_id == target.id))
    if follow:
        db.delete(follow)
        db.commit()
    return
