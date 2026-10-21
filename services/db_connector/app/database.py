from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

# Движок SQLAlchemy с проверкой соединения перед использованием (pool_pre_ping)
engine = create_engine(settings.database_url, pool_pre_ping=True)

# Фабрика сессий: autocommit и autoflush отключены для явного управления транзакциями
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy-моделей проекта."""
    pass


def get_db():
    """
    Генератор сессии БД для внедрения зависимости в FastAPI.
    Гарантирует закрытие соединения после обработки запроса.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
