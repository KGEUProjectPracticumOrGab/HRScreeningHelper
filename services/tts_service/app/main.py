"""
Сервис TTS (Text-to-Speech) — синтез речи.

Текущее поведение: возвращает минимальный беззвучный WAV-файл в формате base64.
Для подключения реального движка OmniVoice — заменить тело функции _build_silent_wav()
на реальный вызов библиотеки синтеза речи.
"""
import base64
import logging
import struct
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TTS Service",
    version="1.0.0",
    description="Сервис синтеза речи (Text-to-Speech). Генерирует аудиофайлы вопросов и системных реплик.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_silent_wav(duration_ms: int = 500, sample_rate: int = 22050) -> bytes:
    """
    Создаёт минимальный беззвучный PCM WAV-файл в памяти.

    Args:
        duration_ms: длительность тишины в миллисекундах
        sample_rate: частота дискретизации (Гц)

    Returns:
        Байты WAV-файла (заголовок + PCM-данные).
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    # 16-битная тишина (нулевые семплы)
    pcm_data = b"\x00\x00" * num_samples

    # WAV-заголовок (формат RIFF PCM)
    data_size = len(pcm_data)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,     # Размер всего чанка
        b"WAVE",
        b"fmt ",
        16,                  # Размер подчанка fmt (PCM)
        1,                   # Формат аудио (1 = PCM)
        1,                   # Количество каналов (моно)
        sample_rate,         # Частота дискретизации
        sample_rate * 2,     # Байт/сек (sample_rate * BlockAlign)
        2,                   # BlockAlign (каналы * байт/семпл)
        16,                  # Бит на семпл
        b"data",
        data_size,
    )
    return header + pcm_data


class SynthesizeRequest(BaseModel):
    """Тело запроса синтеза речи."""
    text: str


@app.post("/synthesize", summary="Синтезировать речь из текста")
async def synthesize(req: SynthesizeRequest):
    """
    Принимает {\"text\": str} и возвращает {\"audio_base64\": str, \"format\": \"wav\"}.

    Для подключения реального TTS (OmniVoice и др.):
    заменить вызов _build_silent_wav() на обращение к библиотеке синтеза речи.
    """
    logger.info("TTS: запрос синтеза речи: %.80s", req.text)
    wav_bytes = _build_silent_wav()
    audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")
    return {"audio_base64": audio_b64, "format": "wav"}


@app.get("/health", tags=["служебные"])
async def health():
    """Проверка работоспособности TTS-сервиса."""
    return {"status": "ok", "service": "tts_service"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
