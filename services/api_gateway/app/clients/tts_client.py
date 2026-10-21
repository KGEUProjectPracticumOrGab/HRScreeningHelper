import base64
import logging
from typing import Optional
import httpx
from ..config import settings

logger = logging.getLogger(__name__)

# Минимальный беззвучный WAV (44 байта) — используется как запасной вариант при ошибке
_SILENT_WAV = (
    b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
    b"D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
)


class TTSClient:
    """
    Клиент синтеза речи (TTS — Text-to-Speech).

    Возвращает аудио в виде base64-строки для передачи через JSON REST API.

    Логика переключения:
      - USE_COLAB_AI_WORKER=true  → POST {COLAB_AI_URL}/tts (удалённый Colab-воркер)
      - USE_COLAB_AI_WORKER=false → POST {TTS_SERVICE_URL}/synthesize (локальный сервис)
    """

    async def synthesize(self, text: str) -> str:
        """Синтезировать речь из текста. Возвращает base64-encoded WAV/MP3."""
        try:
            if settings.use_colab_ai_worker:
                url = f"{settings.colab_ai_url}{settings.colab_tts_endpoint}"
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(url, json={"text": text})
                    resp.raise_for_status()
                    # Colab может возвращать сырые байты или JSON с base64
                    content_type = resp.headers.get("content-type", "")
                    if "application/json" in content_type:
                        data = resp.json()
                        audio_bytes = base64.b64decode(data.get("audio_base64", ""))
                    else:
                        audio_bytes = resp.content
            else:
                url = f"{settings.tts_service_url}/synthesize"
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(url, json={"text": text})
                    resp.raise_for_status()
                    content_type = resp.headers.get("content-type", "")
                    if "application/json" in content_type:
                        data = resp.json()
                        audio_bytes = base64.b64decode(data.get("audio_base64", ""))
                    else:
                        audio_bytes = resp.content

            return base64.b64encode(audio_bytes).decode("utf-8")

        except Exception as exc:
            logger.warning("TTSClient: ошибка синтеза речи: %s — возвращаем беззвучный WAV", exc)
            return base64.b64encode(_SILENT_WAV).decode("utf-8")
