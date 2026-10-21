import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import responses, vacancies, candidates, quest_pools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DBConnector Service",
    version="1.0.0",
    description="Сервис доступа к данным: инкапсулирует все CRUD-операции к PostgreSQL RecruitmentDB.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Создаёт все таблицы БД при старте сервиса, если они ещё не существуют."""
    logger.info("Создание таблиц базы данных...")
    Base.metadata.create_all(bind=engine)
    logger.info("Таблицы базы данных готовы.")


app.include_router(responses.router, prefix="/api/v1")
app.include_router(vacancies.router, prefix="/api/v1")
app.include_router(candidates.router, prefix="/api/v1")
app.include_router(quest_pools.router, prefix="/api/v1")


@app.get("/health", tags=["служебные"])
async def health():
    """Проверка работоспособности DBConnector."""
    return {"status": "ok", "service": "db_connector"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
