"""
Сервис STT (Speech-to-Text) — распознавание речи.

Текущее поведение: возвращает текст-заглушку.
Для подключения реального движка Whisper — раскомментировать соответствующий блок кода ниже.
"""
import logging
import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="STT Service",
    version="1.0.0",
    description="Сервис распознавания речи (Speech-to-Text). Транскрибирует голосовые ответы кандидатов.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/transcribe", summary="Транскрибировать голосовой ответ")
async def transcribe(file: UploadFile = File(...)):
    """
    Принимает аудиофайл (multipart/form-data) и возвращает {\"transcript\": str}.

    Для подключения реального Whisper — раскомментировать блок интеграции ниже.
    Без модели возвращает текст-заглушку.
    """
    audio_bytes = await file.read()
    logger.info(
        "STT: запрос транскрибации: файл=%s, размер=%d байт", file.filename, len(audio_bytes)
    )

    # ── Интеграция с Whisper (раскомментировать при наличии модели) ───────────
    # import whisper, tempfile, os
    # model = whisper.load_model("base")
    # with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
    #     tmp.write(audio_bytes)
    #     tmp_path = tmp.name
    # result = model.transcribe(tmp_path)
    # os.unlink(tmp_path)
    # return {"transcript": result["text"].strip()}
    # ──────────────────────────────────────────────────────────────────────────

    # Заглушка — используется до подключения реального Whisper
    return {"transcript": "[Транскрипция аудио недоступна — Whisper не подключён]"}


@app.get("/health", tags=["служебные"])
async def health():
    """Проверка работоспособности STT-сервиса."""
    return {"status": "ok", "service": "stt_service"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)
