from datetime import datetime
from sqlalchemy import String, ForeignKey, Integer, DateTime, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Follow(Base):
    __tablename__ = "follows"
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    following_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class Like(Base):
    __tablename__ = "likes"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(280), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    posts: Mapped[list["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")

class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    original_post_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id", ondelete="SET NULL"), nullable=True, index=True)

    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reposts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    author: Mapped["User"] = relationship(back_populates="posts")
    original_post: Mapped["Post | None"] = relationship(remote_side=[id])

class Hashtag(Base):
    __tablename__ = "hashtags"
    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(String(64), unique=True, index=True)

class PostHashtag(Base):
    __tablename__ = "post_hashtags"
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    hashtag_id: Mapped[int] = mapped_column(ForeignKey("hashtags.id", ondelete="CASCADE"), primary_key=True)
