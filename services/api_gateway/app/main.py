import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import candidate, screening

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HR Screening Helper — API Gateway",
    version="1.0.0",
    description="Центральный шлюз-оркестратор микросервисной системы HR-скрининга.",
)

# Разрешаем CORS для всех источников (настроить на конкретный домен в продакшне)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(candidate.router)
app.include_router(screening.router)


@app.get("/health", tags=["служебные"])
async def health():
    """Проверка работоспособности API Gateway."""
    return {"status": "ok", "service": "api_gateway"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
