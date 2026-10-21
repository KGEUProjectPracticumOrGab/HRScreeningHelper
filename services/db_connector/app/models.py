from datetime import datetime
from sqlalchemy import (
    Integer, String, Text, Boolean, DateTime, Float,
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from .database import Base


class Project(Base):
    """Таблица проектов — верхний уровень иерархии: Проект → Вакансия → Отклик."""
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Связь 1:N с вакансиями
    vacancies: Mapped[list["Vacancy"]] = relationship("Vacancy", back_populates="project")


class Position(Base):
    """Таблица должностей/направлений (например: 'Junior Python Developer')."""
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Связь с пулами вопросов и вакансиями
    quest_pools: Mapped[list["QuestPool"]] = relationship("QuestPool", back_populates="position")
    vacancies: Mapped[list["Vacancy"]] = relationship("Vacancy", back_populates="position")


class QuestPool(Base):
    """
    Таблица пулов вопросов и эталонных ответов.
    Поля questions и best_answers хранятся в формате JSONB.
    """
    __tablename__ = "quest_pools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    position_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("positions.id"), nullable=True)
    # Массив вопросов для озвучивания кандидату через TTS
    questions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Массив эталонных ответов для сверки через LLM
    best_answers: Mapped[dict] = mapped_column(JSONB, nullable=False)

    position: Mapped["Position | None"] = relationship("Position", back_populates="quest_pools")
    vacancies: Mapped[list["Vacancy"]] = relationship("Vacancy", back_populates="quest_pool")


class Vacancy(Base):
    """Таблица вакансий. Связывает проект, должность и пул вопросов."""
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("projects.id"), nullable=True)
    position_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("positions.id"), nullable=True)
    quest_pool_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("quest_pools.id"), nullable=True)
    # Признак открытой (активной) вакансии
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    project: Mapped["Project | None"] = relationship("Project", back_populates="vacancies")
    position: Mapped["Position | None"] = relationship("Position", back_populates="vacancies")
    quest_pool: Mapped["QuestPool | None"] = relationship("QuestPool", back_populates="vacancies")
    responses: Mapped[list["Response"]] = relationship("Response", back_populates="vacancy")


class Candidate(Base):
    """
    Таблица кандидатов.
    Хранит ФИО, контактные данные и ссылку на резюме.
    Персональные данные обрабатываются в соответствии с 152-ФЗ.
    """
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Контактные данные: Telegram ID, телефон или Email для отправки уведомлений
    contact_info: Mapped[str] = mapped_column(String(255), nullable=False)
    resume_link: Mapped[str | None] = mapped_column(Text, nullable=True)

    responses: Mapped[list["Response"]] = relationship("Response", back_populates="candidate")


class Response(Base):
    """
    Таблица откликов кандидатов на вакансии.
    Поле token — уникальная одноразовая ссылка для авторизации кандидата.
    Поле status отражает текущее состояние в State Machine жизненного цикла отклика.
    """
    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("candidates.id"), nullable=True)
    vacancy_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("vacancies.id"), nullable=True)
    # Уникальный токен для генерации токен-ссылки кандидата
    token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    # Статус жизненного цикла отклика согласно State Machine (см. документацию, гл. 2.3)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="Ожидание скрининга")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    candidate: Mapped["Candidate | None"] = relationship("Candidate", back_populates="responses")
    vacancy: Mapped["Vacancy | None"] = relationship("Vacancy", back_populates="responses")
    # Связь 1:1 с результатом скрининга
    screening_result: Mapped["ScreeningResult | None"] = relationship(
        "ScreeningResult", back_populates="response", uselist=False
    )


class ScreeningResult(Base):
    """
    Таблица результатов скрининга. Связана с откликом 1:1 (UNIQUE на response_id).
    Хранит весь протокол интервью (answers_json), оценки AI и HR, путь к отчёту и решение ЛПР.
    """
    __tablename__ = "screening_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Связь 1:1 с откликом кандидата
    response_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("responses.id"), unique=True, nullable=False
    )
    # Флаг согласия кандидата на обработку ПДн (152-ФЗ)
    accept_pdn: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # Полный транскрипт скрининга в формате JSONB (структура описана в гл. 5.3 документации)
    answers_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Итоговая оценка, выставленная LLM (модулем ИИ)
    ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Независимая оценка HR-специалиста (выставляется до раскрытия ai_score — NFR слепого оценивания)
    hr_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Текстовая характеристика кандидата от HR-специалиста
    hr_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Путь к сгенерированному .docx-отчёту на файловой системе
    report_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Резолюция ЛПР: 'Приглашение на второй этап' или 'Отказ по скринингу'
    lpr_decision: Mapped[str | None] = mapped_column(String(64), nullable=True)

    response: Mapped["Response"] = relationship("Response", back_populates="screening_result")
