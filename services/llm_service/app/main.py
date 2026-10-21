"""
Сервис LLM (Large Language Model) — семантический анализ ответов кандидата.

Текущее поведение: mock-режим со случайными оценками.
Для подключения реальной модели (Qwen, Gemma, Ollama и др.) — заменить блок mock-логики
на реальный вызов модели.
"""
import logging
import random
import uuid
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLM Service",
    version="1.0.0",
    description=(
        "Сервис интеллектуального анализа ответов кандидата. "
        "Сравнивает транскрипты с эталонными ответами и формирует AI-оценку."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    """
    Тело запроса анализа.
    questions: список {question_id, question_text, reference_answer}
    transcripts: словарь {str(question_id): транскрипт_ответа}
    """
    questions: list[dict]
    transcripts: dict[str, str]


@app.post("/analyze", summary="Запустить семантический анализ ответов")
async def analyze(req: AnalyzeRequest):
    """
    Принимает вопросы и транскрипты, возвращает answers_json с AI-оценками.

    Формат ответа соответствует спецификации answers_json (документация, гл. 5.3):
    {session_id, questions: [{..., ai_question_score, ai_comment}], summary_ai_feedback, ai_score}

    Для подключения реальной LLM — заменить mock-блок на вызов модели:
    prompt = build_scoring_prompt(question_text, reference, transcript)
    response = llm.generate(prompt)
    score, comment = parse_llm_response(response)
    """
    logger.info("LLM: запрос анализа: %d вопросов", len(req.questions))

    analysed_questions = []
    total_score = 0.0

    for q in req.questions:
        qid = q.get("question_id", 0)
        transcript = req.transcripts.get(str(qid), "")
        reference = q.get("reference_answer", "")

        # ── Заглушка mock-оценки (заменить на реальный LLM-вызов) ────────────
        if transcript and transcript not in (
            "[Транскрипция аудио недоступна — Whisper не подключён]",
            "[Транскрипция аудио недоступна]",
        ):
            # Кандидат ответил — оценка в диапазоне 6–10
            score = random.randint(6, 10)
            comment = "Ответ соответствует ожиданиям. (mock-оценка)"
        else:
            # Ответ не получен или не распознан — оценка 1–5
            score = random.randint(1, 5)
            comment = "Ответ не получен или не распознан. (mock-оценка)"
        # ──────────────────────────────────────────────────────────────────────

        total_score += score
        analysed_questions.append({
            "question_id": qid,
            "question_text": q.get("question_text", ""),
            "reference_answer": reference,
            "candidate_transcript": transcript,
            "ai_question_score": score,
            "ai_comment": comment,
        })

    ai_score = round(total_score / len(req.questions), 2) if req.questions else 0.0
    summary = (
        f"Кандидат ответил на {len(req.questions)} вопросов. "
        f"Средняя AI-оценка: {ai_score:.1f}/10. "
        "(Оценки сформированы mock-сервисом — реальная LLM недоступна.)"
    )

    return {
        "session_id": str(uuid.uuid4()),
        "questions": analysed_questions,
        "summary_ai_feedback": summary,
        "ai_score": ai_score,
    }


@app.get("/health", tags=["служебные"])
async def health():
    """Проверка работоспособности LLM-сервиса."""
    return {"status": "ok", "service": "llm_service"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8004, reload=True)
