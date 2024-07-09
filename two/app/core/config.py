
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "User Organisation Service"

    DATABASE_URI: str 
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int



    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
