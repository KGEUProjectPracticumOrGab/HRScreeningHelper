"""
Эндпоинты контура HR-специалиста и ЛПР.

Последовательность взаимодействия:
  1. GET  /api/v1/screening/{response_id}/transcript — просмотр транскрипта (слепое оценивание)
  2. POST /api/v1/screening/{response_id}/hr-review  — сохранение HR-оценки → генерация .docx → уведомление ЛПР
  3. GET  /api/v1/screening/{response_id}/report     — скачать .docx-отчёт
  4. POST /api/v1/screening/{response_id}/decision   — решение ЛПР → обратная связь кандидату
"""
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..clients.db_client import DBClient
from ..clients.notifications_client import NotificationsClient
from ..clients.report_client import ReportClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/screening", tags=["контур HR и ЛПР"])

db_client = DBClient()
notif_client = NotificationsClient()
report_client = ReportClient()


# ── 1. Транскрипт (слепое оценивание — без ai_score) ─────────────────────────

@router.get("/{response_id}/transcript", summary="Просмотр транскрипта скрининга")
async def get_transcript(response_id: int):
    """
    Возвращает текстовую расшифровку вопросов и ответов кандидата.

    NFR — Слепое независимое оценивание:
    Поля ai_score, ai_question_score и ai_comment НАМЕРЕННО исключены из ответа.
    HR-специалист выставляет оценку, не зная предварительного результата ИИ.
    Раскрытие ai_score происходит только после сохранения hr_score.
    """
    response = await db_client.get_response(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Отклик не найден")

    screening_result = await db_client.get_screening_result(response_id)
    if not screening_result:
        raise HTTPException(status_code=404, detail="Результат скрининга не найден")

    answers_json = screening_result.get("answers_json") or {}

    # Формируем список вопросов БЕЗ полей AI-оценки (NFR слепого оценивания)
    blind_questions = []
    for q in answers_json.get("questions", []):
        blind_questions.append({
            "question_id": q.get("question_id"),
            "question_text": q.get("question_text"),
            "candidate_transcript": q.get("candidate_transcript"),
        })

    return {
        "response_id": response_id,
        "status": response.get("status"),
        "candidate": response.get("candidate"),
        "session_id": answers_json.get("session_id"),
        "questions": blind_questions,
    }


# ── 2. Оценка HR-специалиста ──────────────────────────────────────────────────

class HrReviewPayload(BaseModel):
    """Тело запроса сохранения оценки HR-специалиста."""
    hr_score: float
    hr_comment: str


@router.post("/{response_id}/hr-review", summary="Сохранить оценку HR-специалиста")
async def submit_hr_review(response_id: int, payload: HrReviewPayload):
    """
    Сохраняет независимую оценку и характеристику от HR-специалиста.

    Затем:
      1. Генерирует сводный .docx-отчёт (ai_score + hr_score + транскрипт)
      2. Сохраняет путь к отчёту в БД
      3. Обновляет статус на 'Отзыв ЛПР'
      4. Отправляет уведомление ЛПР о готовности отчёта
    """
    response = await db_client.get_response(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Отклик не найден")

    if response.get("status") != "HR оценка":
        raise HTTPException(
            status_code=403,
            detail=f"Недоступно. Текущий статус: {response.get('status')}",
        )

    # Сохраняем оценку HR
    await db_client.update_hr_review(response_id, payload.hr_score, payload.hr_comment)

    # Получаем полные данные для генерации отчёта
    screening_result = await db_client.get_screening_result(response_id)
    candidate = response.get("candidate") or {}
    answers_json = (screening_result or {}).get("answers_json") or {}

    report_data = {
        "response_id": response_id,
        "candidate_name": candidate.get("full_name", "Неизвестно"),
        "candidate_contact": candidate.get("contact_info", ""),
        "vacancy_id": response.get("vacancy_id"),
        "answers_json": answers_json,
        "ai_score": (screening_result or {}).get("ai_score"),
        "hr_score": payload.hr_score,
        "hr_comment": payload.hr_comment,
        "lpr_decision": None,
    }

    # Генерация .docx-отчёта через сервис JSONtoWord
    report_path = await report_client.generate_report(report_data)
    if report_path:
        await db_client.update_report_path(response_id, report_path)

    # Статус переходит к контуру ЛПР
    await db_client.update_response_status(response_id, "Отзыв ЛПР")

    # Уведомляем ЛПР о готовности отчёта
    lpr_message = (
        f"HR-оценка завершена для кандидата {candidate.get('full_name', 'Неизвестно')} "
        f"(response_id={response_id}). HR оценка: {payload.hr_score}. "
        f"Требуется решение ЛПР."
    )
    await notif_client.notify(recipient="lpr", message=lpr_message, channel="email")

    return {
        "status": "Отзыв ЛПР",
        "report_path": report_path,
        "message": "HR-оценка сохранена. Отчёт сформирован. Ожидается решение ЛПР.",
    }


# ── 3. Скачать отчёт ──────────────────────────────────────────────────────────

@router.get("/{response_id}/report", summary="Скачать .docx-отчёт по кандидату")
async def download_report(response_id: int):
    """
    Возвращает сформированный .docx-отчёт для ознакомления ЛПР.
    Содержит: данные кандидата, транскрипт, AI-оценку, HR-оценку и решение ЛПР.
    """
    screening_result = await db_client.get_screening_result(response_id)
    if not screening_result:
        raise HTTPException(status_code=404, detail="Результат скрининга не найден")

    report_path = screening_result.get("report_path")
    if not report_path:
        raise HTTPException(status_code=404, detail="Отчёт ещё не сформирован")

    path = Path(report_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Файл отчёта не найден: {report_path}")

    return FileResponse(
        path=str(path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=path.name,
    )


# ── 4. Решение ЛПР ────────────────────────────────────────────────────────────

class LprDecisionPayload(BaseModel):
    """Тело запроса фиксации решения ЛПР."""
    decision: str  # 'approved' (приглашение) | 'rejected' (отказ)


@router.post("/{response_id}/decision", summary="Зафиксировать решение ЛПР")
async def submit_lpr_decision(response_id: int, payload: LprDecisionPayload):
    """
    Фиксирует резолюцию ЛПР и завершает жизненный цикл отклика.

    Обработка:
      1. Проверяет допустимость значения decision
      2. Обновляет lpr_decision в БД
      3. Переводит статус в 'Приглашение на второй этап' или 'Отказ по скринингу'
      4. Генерирует персонализированный текст обратной связи (FeedbackGenerator)
      5. Отправляет письмо кандидату через NotificationsCenter
    """
    if payload.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=422, detail="decision должен быть 'approved' или 'rejected'")

    response = await db_client.get_response(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Отклик не найден")

    if response.get("status") != "Отзыв ЛПР":
        raise HTTPException(
            status_code=403,
            detail=f"Недоступно. Текущий статус: {response.get('status')}",
        )

    # Маппинг решения ЛПР на статус State Machine
    new_status = (
        "Приглашение на второй этап" if payload.decision == "approved" else "Отказ по скринингу"
    )

    await db_client.update_lpr_decision(response_id, payload.decision)
    await db_client.update_response_status(response_id, new_status)

    # Получаем данные для генерации персонализированного фидбека
    screening_result = await db_client.get_screening_result(response_id) or {}
    candidate = response.get("candidate") or {}
    candidate_name = candidate.get("full_name", "Кандидат")
    candidate_contact = candidate.get("contact_info", "")

    feedback_text = await report_client.generate_feedback(
        candidate_name=candidate_name,
        decision=payload.decision,
        hr_comment=screening_result.get("hr_comment") or "",
        ai_score=screening_result.get("ai_score") or 0.0,
        hr_score=screening_result.get("hr_score") or 0.0,
    )

    # Отправляем обратную связь кандидату
    await notif_client.notify(
        recipient=candidate_contact,
        message=feedback_text,
        channel="email",
    )

    return {
        "status": new_status,
        "decision": payload.decision,
        "feedback_sent": True,
        "message": "Решение ЛПР зафиксировано. Обратная связь отправлена кандидату.",
    }
