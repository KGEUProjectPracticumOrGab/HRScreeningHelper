import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/candidates", tags=["кандидаты"])


@router.post("/", response_model=schemas.CandidateRead)
def create_candidate(payload: schemas.CandidateCreate, db: Session = Depends(get_db)):
    """Создать нового кандидата."""
    return crud.create_candidate(db, payload)


@router.get("/{candidate_id}", response_model=schemas.CandidateRead)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Получить кандидата по ID."""
    obj = crud.get_candidate(db, candidate_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Кандидат не найден")
    return obj


@router.get("/", response_model=list[schemas.CandidateRead])
def list_candidates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получить список всех кандидатов с пагинацией."""
    return crud.get_candidates(db, skip=skip, limit=limit)
