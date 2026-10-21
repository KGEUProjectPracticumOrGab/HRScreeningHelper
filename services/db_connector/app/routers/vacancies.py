import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vacancies", tags=["вакансии"])


@router.post("/", response_model=schemas.VacancyRead)
def create_vacancy(payload: schemas.VacancyCreate, db: Session = Depends(get_db)):
    """Создать новую вакансию."""
    return crud.create_vacancy(db, payload)


@router.get("/{vacancy_id}", response_model=schemas.VacancyRead)
def get_vacancy(vacancy_id: int, db: Session = Depends(get_db)):
    """Получить вакансию по ID."""
    obj = crud.get_vacancy(db, vacancy_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
    return obj


@router.get("/", response_model=list[schemas.VacancyRead])
def list_vacancies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список всех вакансий с пагинацией."""
    return crud.get_vacancies(db, skip=skip, limit=limit)


@router.get("/{vacancy_id}/quest-pool", response_model=schemas.QuestPoolRead)
def get_quest_pool_by_vacancy(vacancy_id: int, db: Session = Depends(get_db)):
    """
    Получить пул вопросов, привязанный к вакансии.
    Используется API Gateway для получения вопросов и эталонных ответов во время скрининга.
    """
    obj = crud.get_quest_pool_by_vacancy(db, vacancy_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Пул вопросов для данной вакансии не найден")
    return obj
