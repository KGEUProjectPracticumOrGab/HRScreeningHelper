import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quest-pools", tags=["пулы вопросов"])


@router.post("/", response_model=schemas.QuestPoolRead)
def create_quest_pool(payload: schemas.QuestPoolCreate, db: Session = Depends(get_db)):
    """Создать новый пул вопросов и эталонных ответов."""
    return crud.create_quest_pool(db, payload)


@router.get("/{pool_id}", response_model=schemas.QuestPoolRead)
def get_quest_pool(pool_id: int, db: Session = Depends(get_db)):
    """Получить пул вопросов по ID."""
    obj = crud.get_quest_pool(db, pool_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Пул вопросов не найден")
    return obj
