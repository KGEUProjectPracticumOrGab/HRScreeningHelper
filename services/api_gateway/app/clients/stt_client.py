import logging
from typing import Optional
import httpx
from ..config import settings

logger = logging.getLogger(__name__)


class STTClient:
    """
    Клиент распознавания речи (STT — Speech-to-Text).

    Логика переключения:
      - USE_COLAB_AI_WORKER=true  → POST {COLAB_AI_URL}/stt (удалённый Colab-воркер)
      - USE_COLAB_AI_WORKER=false → POST {STT_SERVICE_URL}/transcribe (локальный Whisper)

    При любой ошибке возвращает заглушку вместо исключения.
    """

    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """
        Транскрибировать аудиофайл в текст.

        Args:
            audio_bytes: байты аудиозаписи кандидата
            filename: имя файла (используется в multipart/form-data)

        Returns:
            Строка транскрипции или заглушка при ошибке.
        """
        try:
            if settings.use_colab_ai_worker:
                url = f"{settings.colab_ai_url}{settings.colab_stt_endpoint}"
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(
                        url,
                        files={"file": (filename, audio_bytes, "audio/wav")},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("transcript", "")
            else:
                url = f"{settings.stt_service_url}/transcribe"
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(
                        url,
                        files={"file": (filename, audio_bytes, "audio/wav")},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("transcript", "")

        except Exception as exc:
            logger.warning("STTClient: ошибка транскрибации: %s — возвращаем заглушку", exc)
            return "[Транскрипция аудио недоступна]"
