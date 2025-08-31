from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, exists, and_
from ..auth import get_db, get_current_user, get_current_user_optional
from .. import schemas
from ..models import User, Post, Like, Hashtag, PostHashtag
from ..utils import extract_hashtags

router = APIRouter(prefix="/posts", tags=["posts"])

def _user_public(db: Session, user: User) -> schemas.UserPublic:
    followers_count = db.scalar(select(func.count()).select_from(User).join_from(User, User.posts, isouter=True).where(User.id == user.id)) or 0
    following_count = 0
    posts_count = db.scalar(select(func.count()).select_from(Post).where(Post.author_id == user.id)) or 0
    return schemas.UserPublic(
        id=user.id, username=user.username, display_name=user.display_name, bio=user.bio,
        followers_count=followers_count, following_count=following_count, posts_count=posts_count,
    )

def _post_to_public(db: Session, post: Post, current_user: User | None = None) -> schemas.PostPublic:
    liked_by_me = False
    reposted_by_me = False
    if current_user:
        liked_by_me = bool(db.scalar(
            select(exists().where(and_(Like.user_id == current_user.id, Like.post_id == post.id)))
        ))
        reposted_by_me = bool(db.scalar(
            select(exists().where(and_(Post.author_id == current_user.id, Post.original_post_id == post.id)))
        ))

    hashtags = []
    # fetch hashtags for post
    tags_stmt = select(Hashtag.tag).join(PostHashtag, Hashtag.id == PostHashtag.hashtag_id).where(PostHashtag.post_id == post.id)
    hashtags = [row[0] for row in db.execute(tags_stmt).all()]
    return schemas.PostPublic(
        id=post.id,
        author=_user_public(db, post.author),
        text=post.text,
        created_at=post.created_at,
        updated_at=post.updated_at,
        edited=post.edited,
        original_post_id=post.original_post_id,
        likes_count=post.likes_count,
        reposts_count=post.reposts_count,
        hashtags=hashtags,
        liked_by_me=liked_by_me,
        reposted_by_me=reposted_by_me
    )

@router.post("", response_model=schemas.PostPublic, status_code=201)
def create_post(payload: schemas.PostCreate, current=Depends(get_current_user), db: Session = Depends(get_db)):
    post = Post(author_id=current.id, text=payload.text)
    db.add(post); db.flush()
    # hashtags
    tags = extract_hashtags(payload.text)
    for t in tags:
        h = db.scalars(select(Hashtag).where(Hashtag.tag == t)).first()
        if not h:
            h = Hashtag(tag=t); db.add(h); db.flush()
        db.add(PostHashtag(post_id=post.id, hashtag_id=h.id))
    db.commit(); db.refresh(post)
    return _post_to_public(db, post)

@router.get("/{post_id}", response_model=schemas.PostPublic)
def get_post(post_id: int, current=Depends(get_current_user_optional), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return _post_to_public(db, post, current)

@router.patch("/{post_id}", response_model=schemas.PostPublic)
def edit_post(post_id: int, payload: schemas.PostUpdate, current=Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current.id:
        raise HTTPException(status_code=403, detail="You can edit only your own posts")
    post.text = payload.text; post.edited = True; post.updated_at = datetime.utcnow()
    db.execute(PostHashtag.__table__.delete().where(PostHashtag.post_id == post.id))
    for t in extract_hashtags(payload.text):
        h = db.scalars(select(Hashtag).where(Hashtag.tag == t)).first()
        if not h:
            h = Hashtag(tag=t); db.add(h); db.flush()
        db.add(PostHashtag(post_id=post.id, hashtag_id=h.id))
    db.commit(); db.refresh(post)
    return _post_to_public(db, post)

@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int, current=Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        return
    if post.author_id != current.id:
        raise HTTPException(status_code=403, detail="You can delete only your own posts")
    db.delete(post); db.commit(); return

@router.post("/{post_id}/like", status_code=204)
def like_post(post_id: int, current=Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    exists = db.execute(select(Like).where(Like.user_id == current.id, Like.post_id == post_id)).scalar()
    if not exists:
        db.add(Like(user_id=current.id, post_id=post_id))
        post.likes_count += 1
        db.commit()
    return

@router.delete("/{post_id}/like", status_code=204)
def unlike_post(post_id: int, current=Depends(get_current_user), db: Session = Depends(get_db)):
    like = db.execute(select(Like).where(Like.user_id == current.id, Like.post_id == post_id)).scalar()
    if like:
        db.delete(like)
        post = db.get(Post, post_id)
        if post and post.likes_count > 0:
            post.likes_count -= 1
        db.commit()
    return

@router.post("/{post_id}/repost", response_model=schemas.PostPublic, status_code=201)
def repost_post(post_id: int, current=Depends(get_current_user), db: Session = Depends(get_db)):
    original = db.get(Post, post_id)
    if not original:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if original.author_id == current.id:
        raise HTTPException(status_code=400, detail="Нельзя репостить свои посты")
    repost = Post(author_id=current.id, text=original.text, original_post_id=original.id)
    db.add(repost); db.flush()
    original.reposts_count += 1
    # copy hashtags
    tags = db.execute(select(PostHashtag.hashtag_id).where(PostHashtag.post_id == original.id)).scalars().all()
    for hid in tags:
        db.add(PostHashtag(post_id=repost.id, hashtag_id=hid))
    db.commit(); db.refresh(repost)
    return _post_to_public(db, repost)



@router.get("", response_model=schemas.FeedResponse)
def list_posts(author: str | None = Query(default=None),
               offset: int = 0, limit: int = Query(20, ge=1, le=100),
               current=Depends(get_current_user_optional), db: Session = Depends(get_db)):
    stmt = select(Post)
    if author:
        # найти user.id по username
        user = db.scalar(select(User).where(User.username == author))
        if not user:
            return schemas.FeedResponse(items=[], next_offset=None)
        stmt = stmt.where(Post.author_id == user.id)

    stmt = stmt.order_by(Post.created_at.desc()).offset(offset).limit(limit)
    items = db.scalars(stmt).all()
    from .posts import _post_to_public
    return schemas.FeedResponse(items=[_post_to_public(db, p, current) for p in items],
                                next_offset=offset + limit if len(items) == limit else None)