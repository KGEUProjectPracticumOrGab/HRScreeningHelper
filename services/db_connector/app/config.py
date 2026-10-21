from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки сервиса DBConnector. Значения читаются из переменных окружения или .env файла."""
    database_url: str = "postgresql://hruser:hrpassword@localhost:5432/recruitmentdb"

    class Config:
        env_file = ".env"


settings = Settings()
