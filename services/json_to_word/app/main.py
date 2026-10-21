"""
Сервис JSONtoWord (JtW) — генерация .docx-отчётов по результатам скрининга.
"""
import logging
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Optional
from .generator import generate_screening_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Директория для сохранения отчётов (настраивается через переменную окружения)
REPORT_OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", "./reports")

app = FastAPI(
    title="JSONtoWord Service",
    version="1.0.0",
    description="Сервис генерации итоговых .docx-отчётов по результатам скрининга кандидатов.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateReportRequest(BaseModel):
    """Тело запроса генерации отчёта."""
    response_id: Any
    candidate_name: str
    candidate_contact: Optional[str] = None
    vacancy_id: Optional[Any] = None
    answers_json: Optional[Any] = None  # Полный транскрипт скрининга (JSONB)
    ai_score: Optional[float] = None
    hr_score: Optional[float] = None
    hr_comment: Optional[str] = None
    lpr_decision: Optional[str] = None


@app.post("/generate", summary="Сгенерировать .docx-отчёт")
async def generate_report(req: GenerateReportRequest):
    """
    Генерирует .docx-отчёт по данным скрининга и возвращает путь к файлу.

    Отчёт содержит: ФИО кандидата, транскрипт вопросов и ответов,
    оценки AI и HR, комментарий HR и решение ЛПР.
    """
    try:
        report_path = generate_screening_report(
            data=req.model_dump(),
            output_dir=REPORT_OUTPUT_DIR,
        )
        return {"report_path": report_path}
    except Exception as exc:
        logger.error("Ошибка генерации отчёта: %s", exc)
        raise HTTPException(status_code=500, detail=f"Ошибка генерации отчёта: {exc}")


@app.get("/health", tags=["служебные"])
async def health():
    """Проверка работоспособности сервиса JSONtoWord."""
    return {"status": "ok", "service": "json_to_word"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8005, reload=True)
