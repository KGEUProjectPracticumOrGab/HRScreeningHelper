import logging
from typing import Optional, Any
from sqlalchemy.orm import Session
from . import models, schemas

logger = logging.getLogger(__name__)


# ── Проекты ───────────────────────────────────────────────────────────────────

def get_project(db: Session, project_id: int) -> Optional[models.Project]:
    """Получить проект по ID."""
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def get_projects(db: Session, skip: int = 0, limit: int = 100) -> list[models.Project]:
    """Получить список проектов с пагинацией."""
    return db.query(models.Project).offset(skip).limit(limit).all()


def create_project(db: Session, project: schemas.ProjectCreate) -> models.Project:
    """Создать новый проект."""
    db_obj = models.Project(**project.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


# ── Должности ─────────────────────────────────────────────────────────────────

def get_position(db: Session, position_id: int) -> Optional[models.Position]:
    """Получить должность по ID."""
    return db.query(models.Position).filter(models.Position.id == position_id).first()


def get_positions(db: Session, skip: int = 0, limit: int = 100) -> list[models.Position]:
    """Получить список должностей с пагинацией."""
    return db.query(models.Position).offset(skip).limit(limit).all()


def create_position(db: Session, position: schemas.PositionCreate) -> models.Position:
    """Создать новую должность."""
    db_obj = models.Position(**position.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


# ── Пулы вопросов ─────────────────────────────────────────────────────────────

def get_quest_pool(db: Session, pool_id: int) -> Optional[models.QuestPool]:
    """Получить пул вопросов по ID."""
    return db.query(models.QuestPool).filter(models.QuestPool.id == pool_id).first()


def get_quest_pool_by_vacancy(db: Session, vacancy_id: int) -> Optional[models.QuestPool]:
    """
    Получить пул вопросов, привязанный к указанной вакансии.
    Используется в API Gateway для получения вопросов и эталонных ответов.
    """
    vacancy = db.query(models.Vacancy).filter(models.Vacancy.id == vacancy_id).first()
    if not vacancy or not vacancy.quest_pool_id:
        return None
    return db.query(models.QuestPool).filter(models.QuestPool.id == vacancy.quest_pool_id).first()


def create_quest_pool(db: Session, pool: schemas.QuestPoolCreate) -> models.QuestPool:
    """Создать новый пул вопросов."""
    db_obj = models.QuestPool(**pool.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


# ── Вакансии ──────────────────────────────────────────────────────────────────

def get_vacancy(db: Session, vacancy_id: int) -> Optional[models.Vacancy]:
    """Получить вакансию по ID."""
    return db.query(models.Vacancy).filter(models.Vacancy.id == vacancy_id).first()


def get_vacancies(db: Session, skip: int = 0, limit: int = 100) -> list[models.Vacancy]:
    """Получить список вакансий с пагинацией."""
    return db.query(models.Vacancy).offset(skip).limit(limit).all()


def create_vacancy(db: Session, vacancy: schemas.VacancyCreate) -> models.Vacancy:
    """Создать новую вакансию."""
    db_obj = models.Vacancy(**vacancy.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


# ── Кандидаты ─────────────────────────────────────────────────────────────────

def get_candidate(db: Session, candidate_id: int) -> Optional[models.Candidate]:
    """Получить кандидата по ID."""
    return db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()


def get_candidates(db: Session, skip: int = 0, limit: int = 100) -> list[models.Candidate]:
    """Получить список кандидатов с пагинацией."""
    return db.query(models.Candidate).offset(skip).limit(limit).all()


def create_candidate(db: Session, candidate: schemas.CandidateCreate) -> models.Candidate:
    """Создать нового кандидата."""
    db_obj = models.Candidate(**candidate.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


# ── Отклики ───────────────────────────────────────────────────────────────────

def get_response(db: Session, response_id: int) -> Optional[models.Response]:
    """Получить отклик по ID."""
    return db.query(models.Response).filter(models.Response.id == response_id).first()


def get_response_by_token(db: Session, token: str) -> Optional[models.Response]:
    """
    Получить отклик по уникальному токену.
    Основной метод авторизации кандидата по токен-ссылке.
    """
    return db.query(models.Response).filter(models.Response.token == token).first()


def get_responses(db: Session, skip: int = 0, limit: int = 100) -> list[models.Response]:
    """Получить список откликов с пагинацией."""
    return db.query(models.Response).offset(skip).limit(limit).all()


def create_response(db: Session, response: schemas.ResponseCreate) -> models.Response:
    """Создать новый отклик (генерация токен-ссылки происходит вне этой функции)."""
    db_obj = models.Response(**response.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_response_status(db: Session, response_id: int, status: str) -> Optional[models.Response]:
    """
    Обновить статус отклика в соответствии с State Machine жизненного цикла.
    Допустимые статусы описаны в документации, гл. 2.3.
    """
    db_obj = db.query(models.Response).filter(models.Response.id == response_id).first()
    if not db_obj:
        return None
    db_obj.status = status
    db.commit()
    db.refresh(db_obj)
    return db_obj


# ── Результаты скрининга ──────────────────────────────────────────────────────

def get_screening_result(db: Session, response_id: int) -> Optional[models.ScreeningResult]:
    """Получить результат скрининга по ID отклика."""
    return db.query(models.ScreeningResult).filter(
        models.ScreeningResult.response_id == response_id
    ).first()


def create_screening_result(
    db: Session, response_id: int, accept_pdn: bool
) -> models.ScreeningResult:
    """
    Создать запись результата скрининга при фиксации решения по ПДн.
    Вызывается сразу после получения ответа кандидата на запрос согласия.
    """
    db_obj = models.ScreeningResult(response_id=response_id, accept_pdn=accept_pdn)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_answers_json(
    db: Session, response_id: int, answers_json: Any
) -> Optional[models.ScreeningResult]:
    """
    Обновить поле answers_json (транскрипт скрининга).
    Вызывается после каждого ответа кандидата и после LLM-анализа.
    """
    db_obj = db.query(models.ScreeningResult).filter(
        models.ScreeningResult.response_id == response_id
    ).first()
    if not db_obj:
        return None
    db_obj.answers_json = answers_json
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_ai_score(
    db: Session, response_id: int, ai_score: float, answers_json: Optional[Any] = None
) -> Optional[models.ScreeningResult]:
    """
    Сохранить итоговую AI-оценку после завершения LLM-анализа.
    Опционально обновляет answers_json с детальными оценками по вопросам.
    """
    db_obj = db.query(models.ScreeningResult).filter(
        models.ScreeningResult.response_id == response_id
    ).first()
    if not db_obj:
        return None
    db_obj.ai_score = ai_score
    if answers_json is not None:
        db_obj.answers_json = answers_json
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_hr_review(
    db: Session, response_id: int, hr_score: float, hr_comment: str
) -> Optional[models.ScreeningResult]:
    """
    Сохранить независимую оценку HR-специалиста.
    Согласно NFR слепого оценивания, HR выставляет оценку до раскрытия ai_score.
    """
    db_obj = db.query(models.ScreeningResult).filter(
        models.ScreeningResult.response_id == response_id
    ).first()
    if not db_obj:
        return None
    db_obj.hr_score = hr_score
    db_obj.hr_comment = hr_comment
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_report_path(
    db: Session, response_id: int, path: str
) -> Optional[models.ScreeningResult]:
    """Сохранить путь к сгенерированному .docx-отчёту после вызова сервиса JSONtoWord."""
    db_obj = db.query(models.ScreeningResult).filter(
        models.ScreeningResult.response_id == response_id
    ).first()
    if not db_obj:
        return None
    db_obj.report_path = path
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_lpr_decision(
    db: Session, response_id: int, decision: str
) -> Optional[models.ScreeningResult]:
    """
    Зафиксировать решение ЛПР.
    Значение decision: 'approved' (приглашение) или 'rejected' (отказ).
    """
    db_obj = db.query(models.ScreeningResult).filter(
        models.ScreeningResult.response_id == response_id
    ).first()
    if not db_obj:
        return None
    db_obj.lpr_decision = decision
    db.commit()
    db.refresh(db_obj)
    return db_obj
