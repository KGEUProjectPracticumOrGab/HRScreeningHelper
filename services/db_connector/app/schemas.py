from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


# ── Проект ────────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    """Схема создания проекта."""
    name: str
    description: Optional[str] = None


class ProjectRead(BaseModel):
    """Схема чтения проекта."""
    id: int
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Должность ─────────────────────────────────────────────────────────────────

class PositionCreate(BaseModel):
    """Схема создания должности/направления."""
    title: str


class PositionRead(BaseModel):
    """Схема чтения должности/направления."""
    id: int
    title: str

    model_config = {"from_attributes": True}


# ── Пул вопросов ──────────────────────────────────────────────────────────────

class QuestPoolCreate(BaseModel):
    """
    Схема создания пула вопросов.
    questions и best_answers — массивы объектов в формате JSONB.
    """
    position_id: Optional[int] = None
    questions: Any
    best_answers: Any


class QuestPoolRead(BaseModel):
    """Схема чтения пула вопросов."""
    id: int
    position_id: Optional[int] = None
    questions: Any
    best_answers: Any

    model_config = {"from_attributes": True}


# ── Вакансия ──────────────────────────────────────────────────────────────────

class VacancyCreate(BaseModel):
    """Схема создания вакансии."""
    project_id: Optional[int] = None
    position_id: Optional[int] = None
    quest_pool_id: Optional[int] = None
    is_active: bool = True


class VacancyRead(BaseModel):
    """Схема чтения вакансии."""
    id: int
    project_id: Optional[int] = None
    position_id: Optional[int] = None
    quest_pool_id: Optional[int] = None
    is_active: bool

    model_config = {"from_attributes": True}


# ── Кандидат ──────────────────────────────────────────────────────────────────

class CandidateCreate(BaseModel):
    """Схема создания кандидата (ввод персональных данных)."""
    full_name: str
    contact_info: str
    resume_link: Optional[str] = None


class CandidateRead(BaseModel):
    """Схема чтения данных кандидата."""
    id: int
    full_name: str
    contact_info: str
    resume_link: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Отклик ────────────────────────────────────────────────────────────────────

class ResponseCreate(BaseModel):
    """Схема создания отклика кандидата на вакансию."""
    candidate_id: Optional[int] = None
    vacancy_id: Optional[int] = None
    token: str
    status: str = "Ожидание скрининга"


class ResponseRead(BaseModel):
    """
    Схема чтения отклика с вложенными данными кандидата.
    Используется в API Gateway для авторизации по токену.
    """
    id: int
    candidate_id: Optional[int] = None
    vacancy_id: Optional[int] = None
    token: str
    status: str
    created_at: datetime
    # Вложенный объект кандидата (eager-load через relationship)
    candidate: Optional[CandidateRead] = None

    model_config = {"from_attributes": True}


class ResponseStatusUpdate(BaseModel):
    """Схема обновления статуса отклика согласно State Machine."""
    status: str


# ── Результат скрининга ───────────────────────────────────────────────────────

class ScreeningResultCreate(BaseModel):
    """Схема создания записи результата скрининга при фиксации решения по ПДн."""
    response_id: int
    accept_pdn: bool


class ScreeningResultRead(BaseModel):
    """Схема чтения полного результата скрининга."""
    id: int
    response_id: int
    accept_pdn: bool
    answers_json: Optional[Any] = None
    ai_score: Optional[float] = None
    hr_score: Optional[float] = None
    hr_comment: Optional[str] = None
    report_path: Optional[str] = None
    lpr_decision: Optional[str] = None

    model_config = {"from_attributes": True}


class AnswersJsonUpdate(BaseModel):
    """Схема обновления поля answers_json (транскрипт скрининга)."""
    answers_json: Any


class AiScoreUpdate(BaseModel):
    """Схема обновления AI-оценки и финального answers_json после LLM-анализа."""
    ai_score: float
    answers_json: Optional[Any] = None


class HrReviewUpdate(BaseModel):
    """Схема сохранения независимой оценки HR-специалиста."""
    hr_score: float
    hr_comment: str


class ReportPathUpdate(BaseModel):
    """Схема сохранения пути к сгенерированному .docx-отчёту."""
    report_path: str


class LprDecisionUpdate(BaseModel):
    """Схема фиксации решения ЛПР ('approved' или 'rejected')."""
    lpr_decision: str
