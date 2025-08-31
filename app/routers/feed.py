from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..auth import get_db, get_current_user, get_current_user_optional
from .. import schemas
from ..models import Post, Follow

router = APIRouter(prefix="/feed", tags=["feed"])

@router.get("/public", response_model=schemas.FeedResponse)
def public_feed(offset: int = 0, limit: int = Query(20, ge=1, le=100), current=Depends(get_current_user_optional), db: Session = Depends(get_db)):
    stmt = (
        select(Post)
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = db.scalars(stmt).all()
    next_offset = offset + limit if len(items) == limit else None

    from .posts import _post_to_public
    return schemas.FeedResponse(items=[_post_to_public(db, p, current) for p in items], next_offset=next_offset)

@router.get("/following", response_model=schemas.FeedResponse)
def following_feed(
    offset: int = 0,
    limit: int = Query(20, ge=1, le=100),
    current=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    subq = select(Follow.following_id).where(Follow.follower_id == current.id)
    stmt = (
        select(Post)
        .where(Post.author_id.in_(subq))
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = db.scalars(stmt).all()
    next_offset = offset + limit if len(items) == limit else None

    from .posts import _post_to_public
    return schemas.FeedResponse(items=[_post_to_public(db, p, current) for p in items], next_offset=next_offset)
