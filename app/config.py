from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    SECRET_KEY: str = Field(default="dev_secret_change_me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    DATABASE_URL: str = Field(default="sqlite:///./app.db")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
