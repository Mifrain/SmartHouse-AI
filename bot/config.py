from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    DATABASE_URL: str = None

    GROQ_API_KEY: str

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def get_database_url(cls, v, info):
        return f"postgresql+asyncpg://{info.data['DB_USER']}:{info.data['DB_PASS']}@{info.data['DB_HOST']}:{info.data['DB_PORT']}/{info.data['DB_NAME']}"


    model_config = SettingsConfigDict(env_file=".env")



settings = Settings()
