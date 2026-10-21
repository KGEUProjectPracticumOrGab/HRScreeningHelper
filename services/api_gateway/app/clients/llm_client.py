import logging
import random
import uuid
from typing import Any
import httpx
from ..config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Клиент семантического анализа (LLM — Large Language Model).

    Сравнивает транскрипты ответов кандидата с эталонными ответами и возвращает
    структурированную оценку в формате answers_json (см. документацию, гл. 5.3).

    Логика переключения:
      - USE_COLAB_AI_WORKER=true  → POST {COLAB_AI_URL}/llm (удалённый Colab-воркер с Qwen/Gemma)
      - USE_COLAB_AI_WORKER=false → POST {LLM_SERVICE_URL}/analyze (локальный mock-сервис)

    При недоступности LLM возвращает mock-анализ со случайными оценками.
    """

    async def analyze(self, questions: list[dict], transcripts: dict[str, str]) -> dict:
        """
        Запустить семантический анализ ответов кандидата.

        Args:
            questions: список словарей {question_id, question_text, reference_answer}
            transcripts: словарь {str(question_id): транскрипт_ответа}

        Returns:
            answers_json — структура со списком вопросов, оценками и summary_ai_feedback.
        """
        try:
            payload = {"questions": questions, "transcripts": transcripts}

            if settings.use_colab_ai_worker:
                url = f"{settings.colab_ai_url}{settings.colab_llm_endpoint}"
            else:
                url = f"{settings.llm_service_url}/analyze"

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()

        except Exception as exc:
            logger.warning("LLMClient: ошибка анализа: %s — возвращаем mock-анализ", exc)
            return self._mock_analysis(questions, transcripts)

    def _mock_analysis(self, questions: list[dict], transcripts: dict[str, str]) -> dict:
        """
        Запасной mock-анализ при недоступности LLM.
        Генерирует случайные оценки в диапазоне 5–10.
        """
        analysed_questions = []
        total_score = 0.0

        for q in questions:
            qid = q.get("question_id", 0)
            score = random.randint(5, 10)
            total_score += score
            analysed_questions.append({
                "question_id": qid,
                "question_text": q.get("question_text", ""),
                "reference_answer": q.get("reference_answer", ""),
                "candidate_transcript": transcripts.get(str(qid), ""),
                "ai_question_score": score,
                "ai_comment": "Mock-оценка — LLM сервис недоступен.",
            })

        ai_score = round(total_score / len(questions), 2) if questions else 0.0
        return {
            "session_id": str(uuid.uuid4()),
            "questions": analysed_questions,
            "summary_ai_feedback": f"Mock-анализ завершён. Средняя оценка: {ai_score}",
            "ai_score": ai_score,
        }
