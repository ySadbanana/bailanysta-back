from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..auth import get_db, get_current_user_optional
from .. import schemas
from ..models import Post, Hashtag, PostHashtag

router = APIRouter(prefix="/search", tags=["search"])

@router.get("", response_model=schemas.FeedResponse)
def search(q: str = Query(..., min_length=1), offset: int = 0, limit: int = Query(20, ge=1, le=100), current=Depends(get_current_user_optional),  db: Session = Depends(get_db)):
    terms = [t for t in q.strip().split() if t]
    posts_stmt = select(Post)

    tags = [t[1:].lower() for t in terms if t.startswith("#")]
    if tags:
        posts_stmt = posts_stmt.join(PostHashtag, PostHashtag.post_id == Post.id).join(Hashtag, Hashtag.id == PostHashtag.hashtag_id)
        posts_stmt = posts_stmt.where(Hashtag.tag.in_(tags))

    for kw in [t for t in terms if not t.startswith("#")]:
        posts_stmt = posts_stmt.where(Post.text.ilike(f"%{kw}%"))

    stmt = posts_stmt.order_by(Post.created_at.desc()).offset(offset).limit(limit)
    items = db.scalars(stmt).all()
    next_offset = offset + limit if len(items) == limit else None

    from .posts import _post_to_public
    return schemas.FeedResponse(items=[_post_to_public(db, p, current) for p in items], next_offset=next_offset)
