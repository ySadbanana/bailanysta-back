import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .database import engine
from .models import Base
from .routers import auth as auth_router
from .routers import users as users_router
from .routers import posts as posts_router
from .routers import feed as feed_router
from .routers import search as search_router

app = FastAPI(title="Bailanysta API")

origins = os.getenv("CORS_ORIGINS", "*")
origins_list = [o.strip() for o in origins.split(",")] if origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(posts_router.router)
app.include_router(feed_router.router)
app.include_router(search_router.router)

@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
