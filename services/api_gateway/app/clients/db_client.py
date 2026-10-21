import logging
from typing import Any, Optional
import httpx
from ..config import settings

logger = logging.getLogger(__name__)

# Базовый URL сервиса DBConnector
_BASE = settings.db_connector_url + "/api/v1"


class DBClient:
    """
    Асинхронный HTTP-клиент к микросервису DBConnector.
    Инкапсулирует все CRUD-запросы к базе данных через REST API.
    При любой ошибке логирует её и возвращает None вместо исключения.
    """

    # ── Отклики ───────────────────────────────────────────────────────────────

    async def get_response_by_token(self, token: str) -> Optional[dict]:
        """Получить отклик по уникальному токену (авторизация кандидата)."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{_BASE}/responses/by-token/{token}")
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("DBClient.get_response_by_token: %s", exc)
            return None

    async def get_response(self, response_id: int) -> Optional[dict]:
        """Получить отклик по ID."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{_BASE}/responses/{response_id}")
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("DBClient.get_response: %s", exc)
            return None

    async def update_response_status(self, response_id: int, status: str) -> Optional[dict]:
        """Обновить статус отклика согласно State Machine жизненного цикла."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.patch(
                    f"{_BASE}/responses/{response_id}/status",
                    json={"status": status},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("DBClient.update_response_status: %s", exc)
            return None

    # ── Результат скрининга ───────────────────────────────────────────────────

    async def create_screening_result(self, response_id: int, accept_pdn: bool) -> Optional[dict]:
        """Создать запись результата скрининга при фиксации ответа по ПДн."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{_BASE}/responses/{response_id}/screening-result",
                    json={"response_id": response_id, "accept_pdn": accept_pdn},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("DBClient.create_screening_result: %s", exc)
            return None

    async def get_screening_result(self, response_id: int) -> Optional[dict]:
        """Получить результат скрининга по ID отклика."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{_BASE}/responses/{response_id}/screening-result")
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("DBClient.get_screening_result: %s", exc)
            return None

    async def update_answers_json(self, response_id: int, answers_json: Any) -> Optional[dict]:
        """Обновить транскрипт скрининга (answers_json в формате JSONB)."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.patch(
                    f"{_BASE}/responses/{response_id}/screening-result/answers",
                    json={"answers_json": answers_json},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("DBClient.update_answers_json: %s", exc)
            return None

    async def update_ai_score(
        self, response_id: int, ai_score: float, answers_json: Optional[Any] = None
    ) -> Optional[dict]:
        """Сохранить AI-оценку и финальный answers_json после LLM-анализа."""
        try:
            payload: dict = {"ai_score": ai_score}
            if answers_json is not None:
                payload["answers_json"] = answers_json
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.patch(
                    f"{_BASE}/responses/{response_id}/screening-result/ai-score",
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("DBClient.update_ai_score: %s", exc)
            return None

    async def update_hr_review(
        self, response_id: int, hr_score: float, hr_comment: str
    ) -> Optional[dict]:
        """Сохранить независимую оценку HR-специалиста (hr_score и hr_comment)."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.patch(
                    f"{_BASE}/responses/{response_id}/screening-result/hr-review",
                    json={"hr_score": hr_score, "hr_comment": hr_comment},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("DBClient.update_hr_review: %s", exc)
            return None

    async def update_report_path(self, response_id: int, path: str) -> Optional[dict]:
        """Сохранить путь к сгенерированному .docx-отчёту."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.patch(
                    f"{_BASE}/responses/{response_id}/screening-result/report-path",
                    json={"report_path": path},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("DBClient.update_report_path: %s", exc)
            return None

    async def update_lpr_decision(self, response_id: int, decision: str) -> Optional[dict]:
        """Зафиксировать решение ЛПР ('approved' / 'rejected')."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.patch(
                    f"{_BASE}/responses/{response_id}/screening-result/lpr-decision",
                    json={"lpr_decision": decision},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("DBClient.update_lpr_decision: %s", exc)
            return None

    async def get_quest_pool_by_vacancy(self, vacancy_id: int) -> Optional[dict]:
        """Получить пул вопросов, привязанный к вакансии (нужен для TTS вопросов и LLM анализа)."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{_BASE}/vacancies/{vacancy_id}/quest-pool")
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            logger.error("DBClient.get_quest_pool_by_vacancy: %s", exc)
            return None
