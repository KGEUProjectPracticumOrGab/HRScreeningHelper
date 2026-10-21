"""
Эндпоинты контура кандидата — сессия голосового скрининга.

Последовательность взаимодействия:
  1. GET  /api/v1/session/{token}          — вход по токен-ссылке
  2. POST /api/v1/session/{token}/pdn      — передача решения по ПДн (согласие/отказ)
  3. GET  /api/v1/session/{token}/question — получение очередного вопроса + аудио (TTS)
  4. POST /api/v1/session/{token}/answer   — загрузка голосового ответа (STT-транскрибация)
  5. POST /api/v1/session/{token}/finish   — завершение скрининга (LLM-анализ → уведомление HR)
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from ..clients.db_client import DBClient
from ..clients.tts_client import TTSClient
from ..clients.stt_client import STTClient
from ..clients.llm_client import LLMClient
from ..clients.notifications_client import NotificationsClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/session", tags=["контур кандидата"])

db_client = DBClient()
tts_client = TTSClient()
stt_client = STTClient()
llm_client = LLMClient()
notif_client = NotificationsClient()

# Текст согласия на обработку ПДн (152-ФЗ)
PDN_TEXT = (
    "Настоящим я даю согласие на обработку моих персональных данных "
    "в соответствии с Федеральным законом № 152-ФЗ «О персональных данных». "
    "Мои данные будут использоваться исключительно для целей подбора персонала."
)

# Шаблон текста голосового приветствия
GREETING_TEXT_TEMPLATE = (
    "Здравствуйте, {name}! Добро пожаловать в систему автоматизированного "
    "HR-скрининга. Перед началом собеседования вам будет предложено ознакомиться "
    "с условиями обработки персональных данных."
)


# ── 1. Вход по токен-ссылке ───────────────────────────────────────────────────

@router.get("/{token}", summary="Вход по токен-ссылке")
async def enter_session(token: str):
    """
    Первичный вход кандидата по уникальной токен-ссылке.

    Возвращает профиль кандидата, статус сессии, аудио приветствия (base64)
    и текст согласия на обработку ПДн.

    Защита от повторного прохождения: возвращает 403, если статус ≠ 'Ожидание скрининга'.
    """
    response = await db_client.get_response_by_token(token)
    if not response:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    # Защита от повторного использования токен-ссылки (NFR — одноразовость)
    if response["status"] != "Ожидание скрининга":
        raise HTTPException(
            status_code=403,
            detail=f"Сессия недоступна. Текущий статус: {response['status']}",
        )

    candidate = response.get("candidate") or {}
    candidate_name = candidate.get("full_name", "Кандидат")
    greeting_text = GREETING_TEXT_TEMPLATE.format(name=candidate_name)

    # Синтез голосового приветствия через TTS
    audio_base64 = await tts_client.synthesize(greeting_text)

    return {
        "response_id": response["id"],
        "status": response["status"],
        "candidate": candidate,
        "greeting_audio_base64": audio_base64,
        "pdn_text": PDN_TEXT,
    }


# ── 2. Передача решения по ПДн ────────────────────────────────────────────────

class PdnPayload(BaseModel):
    """Тело запроса согласия/отказа от обработки ПДн."""
    accept_pdn: bool


@router.post("/{token}/pdn", summary="Передача решения по согласию на ПДн")
async def submit_pdn(token: str, payload: PdnPayload):
    """
    Фиксирует решение кандидата по обработке персональных данных.

    - accept_pdn=true  → создаёт screening_result, инициализирует answers_json, статус 'Процесс скрининга'
    - accept_pdn=false → статус 'Отказ от обработки ПДн', дальнейший опрос заблокирован (152-ФЗ)
    """
    response = await db_client.get_response_by_token(token)
    if not response:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    if response["status"] != "Ожидание скрининга":
        raise HTTPException(status_code=403, detail="ПДн уже были обработаны")

    response_id = response["id"]

    if not payload.accept_pdn:
        # Кандидат отказался от обработки ПДн — блокируем дальнейший опрос
        await db_client.update_response_status(response_id, "Отказ от обработки ПДн")
        await db_client.create_screening_result(response_id, accept_pdn=False)
        return {"status": "Отказ от обработки ПДн", "message": "Обработка персональных данных отклонена."}

    # Кандидат дал согласие — создаём запись скрининга и инициализируем answers_json
    await db_client.create_screening_result(response_id, accept_pdn=True)
    await db_client.update_response_status(response_id, "Процесс скрининга")

    # Инициализация пустого протокола скрининга
    initial_answers = {
        "session_id": str(uuid.uuid4()),
        "questions": [],
        "summary_ai_feedback": "",
    }
    await db_client.update_answers_json(response_id, initial_answers)

    return {"status": "Процесс скрининга", "message": "Согласие получено. Скрининг начат."}


# ── 3. Получение очередного вопроса ──────────────────────────────────────────

@router.get("/{token}/question", summary="Получить очередной вопрос скрининга")
async def get_next_question(token: str):
    """
    Возвращает следующий неотвеченный вопрос из QuestPool с синтезированным аудио (TTS).

    Пагинация по отвеченным question_id: вопрос считается отвеченным,
    если в answers_json заполнено поле candidate_transcript.

    Возвращает {finished: True} когда все вопросы отвечены.
    """
    response = await db_client.get_response_by_token(token)
    if not response:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    if response["status"] not in ("Процесс скрининга",):
        raise HTTPException(status_code=403, detail="Скрининг не активен")

    vacancy_id = response.get("vacancy_id")
    if not vacancy_id:
        raise HTTPException(status_code=500, detail="Вакансия не привязана к отклику")

    quest_pool = await db_client.get_quest_pool_by_vacancy(vacancy_id)
    if not quest_pool:
        raise HTTPException(status_code=404, detail="Пул вопросов не найден")

    questions: list = quest_pool.get("questions", [])
    if not questions:
        raise HTTPException(status_code=404, detail="Вопросы в пуле не найдены")

    # Определяем уже отвеченные question_id по наличию candidate_transcript
    screening_result = await db_client.get_screening_result(response["id"])
    answered_ids: set = set()
    if screening_result and screening_result.get("answers_json"):
        answered_ids = {
            q["question_id"]
            for q in screening_result["answers_json"].get("questions", [])
            if q.get("candidate_transcript")
        }

    # Ищем первый неотвеченный вопрос
    next_question = None
    for q in questions:
        if q.get("question_id") not in answered_ids:
            next_question = q
            break

    if next_question is None:
        return {"finished": True, "message": "Все вопросы отвечены. Пожалуйста, завершите сессию."}

    question_text = next_question.get("question_text", "")
    # Синтез аудио вопроса через TTS
    audio_base64 = await tts_client.synthesize(question_text)

    return {
        "finished": False,
        "question_id": next_question.get("question_id"),
        "question_text": question_text,
        "question_audio_base64": audio_base64,
        "total_questions": len(questions),
        "answered_count": len(answered_ids),
    }


# ── 4. Загрузка голосового ответа ─────────────────────────────────────────────

@router.post("/{token}/answer", summary="Загрузить голосовой ответ кандидата")
async def submit_answer(
    token: str,
    question_id: int = Form(...),
    audio: UploadFile = File(...),
):
    """
    Принимает голосовой ответ кандидата (multipart/form-data).

    Обработка:
      1. Читает аудиофайл
      2. Отправляет в STT для транскрибации
      3. Сохраняет транскрипт в answers_json по question_id

    Запись и транскрибация доступны только при статусе 'Процесс скрининга'
    (согласие на ПДн уже получено — требование 152-ФЗ).
    """
    response = await db_client.get_response_by_token(token)
    if not response:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    if response["status"] != "Процесс скрининга":
        raise HTTPException(status_code=403, detail="Скрининг не активен")

    response_id = response["id"]

    # Транскрибация аудиоответа через STT
    audio_bytes = await audio.read()
    transcript = await stt_client.transcribe(audio_bytes, filename=audio.filename or "audio.wav")

    # Загружаем текущий answers_json из БД
    screening_result = await db_client.get_screening_result(response_id)
    answers_json: dict = {}
    if screening_result and screening_result.get("answers_json"):
        answers_json = screening_result["answers_json"]
    else:
        answers_json = {"session_id": str(uuid.uuid4()), "questions": [], "summary_ai_feedback": ""}

    # Обновляем или добавляем запись по question_id
    questions_list: list = answers_json.get("questions", [])
    found = False
    for entry in questions_list:
        if entry.get("question_id") == question_id:
            entry["candidate_transcript"] = transcript
            found = True
            break

    if not found:
        # Первый ответ на данный вопрос — получаем текст и эталон из пула
        vacancy_id = response.get("vacancy_id")
        quest_pool = await db_client.get_quest_pool_by_vacancy(vacancy_id) if vacancy_id else None
        question_text = ""
        reference_answer = ""
        if quest_pool:
            for q in quest_pool.get("questions", []):
                if q.get("question_id") == question_id:
                    question_text = q.get("question_text", "")
                    break
            for ba in quest_pool.get("best_answers", []):
                if ba.get("question_id") == question_id:
                    reference_answer = ba.get("answer", "")
                    break

        questions_list.append({
            "question_id": question_id,
            "question_text": question_text,
            "reference_answer": reference_answer,
            "candidate_transcript": transcript,
            "ai_question_score": None,
            "ai_comment": None,
        })

    answers_json["questions"] = questions_list
    await db_client.update_answers_json(response_id, answers_json)

    return {"status": "сохранено", "question_id": question_id, "transcript_preview": transcript[:200]}


# ── 5. Завершение сессии ──────────────────────────────────────────────────────

@router.post("/{token}/finish", summary="Завершить сессию скрининга")
async def finish_session(token: str):
    """
    Завершает сессию кандидата и запускает полный цикл постобработки:

    1. Получает собранные транскрипты из answers_json
    2. Получает эталонные ответы из QuestPool
    3. Отправляет данные в LLM для семантического анализа
    4. Сохраняет ai_score и финальный answers_json в БД
    5. Обновляет статус: 'ИИ оценка' → 'HR оценка'
    6. Уведомляет HR-специалиста о завершении скрининга
    7. Синтезирует прощальное аудио через TTS и возвращает его кандидату
    """
    response = await db_client.get_response_by_token(token)
    if not response:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    if response["status"] != "Процесс скрининга":
        raise HTTPException(status_code=403, detail="Скрининг не активен")

    response_id = response["id"]
    vacancy_id = response.get("vacancy_id")

    # Получаем текущий результат со всеми собранными транскриптами
    screening_result = await db_client.get_screening_result(response_id)
    if not screening_result:
        raise HTTPException(status_code=500, detail="Результат скрининга не найден")

    answers_json: dict = screening_result.get("answers_json") or {
        "session_id": str(uuid.uuid4()), "questions": [], "summary_ai_feedback": ""
    }
    questions_with_transcripts: list = answers_json.get("questions", [])

    # Получаем эталонные ответы из пула вопросов
    quest_pool = await db_client.get_quest_pool_by_vacancy(vacancy_id) if vacancy_id else None

    # Формируем данные для LLM-анализа
    llm_questions = []
    transcripts_map: dict[str, str] = {}

    if quest_pool:
        pool_questions: list = quest_pool.get("questions", [])
        best_answers: list = quest_pool.get("best_answers", [])
        # Словарь эталонных ответов: {question_id: эталонный_ответ}
        ref_map = {ba.get("question_id"): ba.get("answer", "") for ba in best_answers}

        for pq in pool_questions:
            qid = pq.get("question_id")
            # Находим транскрипт для данного вопроса
            transcript = ""
            for aq in questions_with_transcripts:
                if aq.get("question_id") == qid:
                    transcript = aq.get("candidate_transcript", "")
                    break
            llm_questions.append({
                "question_id": qid,
                "question_text": pq.get("question_text", ""),
                "reference_answer": ref_map.get(qid, ""),
            })
            transcripts_map[str(qid)] = transcript
    else:
        # Пул вопросов недоступен — используем уже собранные данные
        for q in questions_with_transcripts:
            qid = q.get("question_id")
            llm_questions.append({
                "question_id": qid,
                "question_text": q.get("question_text", ""),
                "reference_answer": q.get("reference_answer", ""),
            })
            transcripts_map[str(qid)] = q.get("candidate_transcript", "")

    # Переводим статус в 'ИИ оценка' и запускаем LLM-анализ
    await db_client.update_response_status(response_id, "ИИ оценка")
    llm_result = await llm_client.analyze(llm_questions, transcripts_map)

    ai_score = llm_result.get("ai_score", 0.0)
    final_answers_json = {
        "session_id": answers_json.get("session_id", str(uuid.uuid4())),
        "questions": llm_result.get("questions", questions_with_transcripts),
        "summary_ai_feedback": llm_result.get("summary_ai_feedback", ""),
    }

    # Сохраняем AI-оценку и финальный транскрипт
    await db_client.update_ai_score(response_id, ai_score, final_answers_json)
    # Статус переходит в 'HR оценка' — ожидаем независимой оценки от HR-специалиста
    await db_client.update_response_status(response_id, "HR оценка")

    # Уведомляем HR-специалиста о завершении скрининга
    candidate = response.get("candidate") or {}
    candidate_name = candidate.get("full_name", "Кандидат")
    hr_message = (
        f"Кандидат {candidate_name} завершил скрининг. "
        f"AI оценка: {ai_score:.1f}. Требуется HR-проверка (response_id={response_id})."
    )
    await notif_client.notify(
        recipient="hr",
        message=hr_message,
        channel="email",
    )

    # Синтез прощальной реплики через TTS
    farewell_text = (
        f"Спасибо, {candidate_name}! Скрининг завершён. "
        "Наш специалист свяжется с вами в ближайшее время."
    )
    farewell_audio = await tts_client.synthesize(farewell_text)

    return {
        "status": "HR оценка",
        "message": "Скрининг завершён. Ожидайте связи с HR.",
        "farewell_audio_base64": farewell_audio,
        "ai_score": ai_score,
    }
