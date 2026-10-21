import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/responses", tags=["отклики"])


@router.post("/", response_model=schemas.ResponseRead)
def create_response(payload: schemas.ResponseCreate, db: Session = Depends(get_db)):
    """Создать новый отклик кандидата на вакансию."""
    return crud.create_response(db, payload)


@router.get("/{response_id}", response_model=schemas.ResponseRead)
def get_response(response_id: int, db: Session = Depends(get_db)):
    """Получить отклик по ID."""
    obj = crud.get_response(db, response_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Отклик не найден")
    return obj


@router.get("/by-token/{token}", response_model=schemas.ResponseRead)
def get_response_by_token(token: str, db: Session = Depends(get_db)):
    """
    Получить отклик по уникальному токену.
    Основной метод входа кандидата по токен-ссылке.
    """
    obj = crud.get_response_by_token(db, token)
    if not obj:
        raise HTTPException(status_code=404, detail="Отклик не найден")
    return obj


@router.get("/", response_model=list[schemas.ResponseRead])
def list_responses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список всех откликов с пагинацией."""
    return crud.get_responses(db, skip=skip, limit=limit)


@router.patch("/{response_id}/status", response_model=schemas.ResponseRead)
def update_status(response_id: int, payload: schemas.ResponseStatusUpdate, db: Session = Depends(get_db)):
    """
    Обновить статус отклика согласно State Machine.
    Допустимые значения описаны в документации, гл. 2.3.
    """
    obj = crud.update_response_status(db, response_id, payload.status)
    if not obj:
        raise HTTPException(status_code=404, detail="Отклик не найден")
    return obj


# ── Результат скрининга ───────────────────────────────────────────────────────

@router.post("/{response_id}/screening-result", response_model=schemas.ScreeningResultRead)
def create_screening_result(
    response_id: int, payload: schemas.ScreeningResultCreate, db: Session = Depends(get_db)
):
    """
    Создать запись результата скрининга при фиксации ответа по ПДн.
    Возвращает 409 если запись уже существует (idempotency guard).
    """
    existing = crud.get_screening_result(db, response_id)
    if existing:
        raise HTTPException(status_code=409, detail="Результат скрининга уже существует")
    return crud.create_screening_result(db, response_id, payload.accept_pdn)


@router.get("/{response_id}/screening-result", response_model=schemas.ScreeningResultRead)
def get_screening_result(response_id: int, db: Session = Depends(get_db)):
    """Получить результат скрининга по ID отклика."""
    obj = crud.get_screening_result(db, response_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Результат скрининга не найден")
    return obj


@router.patch("/{response_id}/screening-result/answers", response_model=schemas.ScreeningResultRead)
def update_answers_json(
    response_id: int, payload: schemas.AnswersJsonUpdate, db: Session = Depends(get_db)
):
    """Обновить поле answers_json (транскрипт скрининга в формате JSONB)."""
    obj = crud.update_answers_json(db, response_id, payload.answers_json)
    if not obj:
        raise HTTPException(status_code=404, detail="Результат скрининга не найден")
    return obj


@router.patch("/{response_id}/screening-result/ai-score", response_model=schemas.ScreeningResultRead)
def update_ai_score(
    response_id: int, payload: schemas.AiScoreUpdate, db: Session = Depends(get_db)
):
    """Сохранить AI-оценку и финальный answers_json после LLM-анализа."""
    obj = crud.update_ai_score(db, response_id, payload.ai_score, payload.answers_json)
    if not obj:
        raise HTTPException(status_code=404, detail="Результат скрининга не найден")
    return obj


@router.patch("/{response_id}/screening-result/hr-review", response_model=schemas.ScreeningResultRead)
def update_hr_review(
    response_id: int, payload: schemas.HrReviewUpdate, db: Session = Depends(get_db)
):
    """Сохранить независимую оценку HR-специалиста (hr_score и hr_comment)."""
    obj = crud.update_hr_review(db, response_id, payload.hr_score, payload.hr_comment)
    if not obj:
        raise HTTPException(status_code=404, detail="Результат скрининга не найден")
    return obj


@router.patch("/{response_id}/screening-result/report-path", response_model=schemas.ScreeningResultRead)
def update_report_path(
    response_id: int, payload: schemas.ReportPathUpdate, db: Session = Depends(get_db)
):
    """Сохранить путь к сгенерированному .docx-отчёту."""
    obj = crud.update_report_path(db, response_id, payload.report_path)
    if not obj:
        raise HTTPException(status_code=404, detail="Результат скрининга не найден")
    return obj


@router.patch("/{response_id}/screening-result/lpr-decision", response_model=schemas.ScreeningResultRead)
def update_lpr_decision(
    response_id: int, payload: schemas.LprDecisionUpdate, db: Session = Depends(get_db)
):
    """Зафиксировать решение ЛПР ('approved' / 'rejected')."""
    obj = crud.update_lpr_decision(db, response_id, payload.lpr_decision)
    if not obj:
        raise HTTPException(status_code=404, detail="Результат скрининга не найден")
    return obj
