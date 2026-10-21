import logging
from typing import Optional
import httpx
from ..config import settings

logger = logging.getLogger(__name__)


class ReportClient:
    """
    HTTP-клиент к сервисам генерации документов и обратной связи:
      - json_to_word (JtW): генерация .docx-отчёта
      - feedback_generator (FG): генерация персонализированного текста обратной связи
    """

    async def generate_report(self, report_data: dict) -> Optional[str]:
        """
        Вызвать сервис JSONtoWord для генерации .docx-отчёта.

        Args:
            report_data: словарь с данными кандидата, answers_json, оценками и решением ЛПР

        Returns:
            Путь к сгенерированному файлу или None при ошибке.
        """
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{settings.json_to_word_url}/generate",
                    json=report_data,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("report_path")
        except Exception as exc:
            logger.warning("ReportClient.generate_report: ошибка генерации отчёта: %s", exc)
            return None

    async def generate_feedback(
        self,
        candidate_name: str,
        decision: str,
        hr_comment: str,
        ai_score: float,
        hr_score: float,
    ) -> str:
        """
        Вызвать FeedbackGenerator для создания персонализированного текста обратной связи.

        Args:
            candidate_name: ФИО кандидата
            decision: 'approved' (приглашение) или 'rejected' (отказ)
            hr_comment: комментарий HR-специалиста
            ai_score: оценка ИИ
            hr_score: оценка HR

        Returns:
            Готовый текст письма обратной связи.
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{settings.feedback_generator_url}/generate",
                    json={
                        "candidate_name": candidate_name,
                        "decision": decision,
                        "hr_comment": hr_comment,
                        "ai_score": ai_score,
                        "hr_score": hr_score,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("feedback_text", "Благодарим за участие в скрининге.")
        except Exception as exc:
            logger.warning("ReportClient.generate_feedback: ошибка генерации фидбека: %s", exc)
            return "Благодарим за участие в скрининге."
