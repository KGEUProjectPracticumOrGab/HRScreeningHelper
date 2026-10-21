"""
Сервис NotificationsCenter (NotC) — центр уведомлений.

Отправляет уведомления через два канала:
  - Telegram: Bot API (chat_id кандидата/HR/ЛПР)
  - Email: SMTP через aiosmtplib

Специальные ключевые слова для recipient:
  'hr', 'lpr', 'hr-team', 'lpr-team' → используется NOTIFICATION_EMAIL из .env
"""
import logging
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Конфигурация из переменных окружения ─────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
# Email по умолчанию для уведомлений HR и ЛПР (ключевые слова 'hr', 'lpr')
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "")

app = FastAPI(
    title="NotificationsCenter Service",
    version="1.0.0",
    description=(
        "Центр уведомлений. Отправляет оповещения HR-специалисту, ЛПР "
        "и финальную обратную связь кандидату через Telegram или Email."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class NotifyRequest(BaseModel):
    """Тело запроса отправки уведомления."""
    recipient: str          # email-адрес, Telegram chat_id или ключевое слово ('hr', 'lpr')
    message: str            # Текст уведомления
    channel: str = "email"  # Канал: 'telegram' | 'email'


async def _send_telegram(chat_id: str, text: str) -> bool:
    """
    Отправляет сообщение через Telegram Bot API.

    Args:
        chat_id: Telegram chat_id получателя
        text: текст сообщения

    Returns:
        True при успешной отправке, False при ошибке или отсутствии токена.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN не задан — пропускаем Telegram-уведомление")
        return False
    try:
        import httpx
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json={"chat_id": chat_id, "text": text})
            resp.raise_for_status()
            logger.info("Telegram-уведомление отправлено получателю: %s", chat_id)
            return True
    except Exception as exc:
        logger.error("Ошибка отправки Telegram-сообщения: %s", exc)
        return False


async def _send_email(to_address: str, subject: str, body: str) -> bool:
    """
    Отправляет письмо через SMTP с TLS (aiosmtplib).

    Ключевые слова 'hr', 'lpr' автоматически заменяются на NOTIFICATION_EMAIL из .env.

    Args:
        to_address: email-адрес или ключевое слово ('hr', 'lpr')
        subject: тема письма
        body: тело письма (plain text)

    Returns:
        True при успешной отправке, False при ошибке или отсутствии учётных данных SMTP.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP-учётные данные не заданы — пропускаем email-уведомление")
        return False
    try:
        import aiosmtplib
        from email.mime.text import MIMEText

        # Разрешаем ключевые слова 'hr' и 'lpr' в реальный email из конфига
        actual_recipient = to_address
        if to_address.lower() in ("hr", "lpr", "hr-team", "lpr-team"):
            actual_recipient = NOTIFICATION_EMAIL

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = actual_recipient

        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info("Email отправлен получателю: %s", actual_recipient)
        return True
    except Exception as exc:
        logger.error("Ошибка отправки email: %s", exc)
        return False


@app.post("/notify", summary="Отправить уведомление")
async def notify(req: NotifyRequest):
    """
    Отправляет уведомление через указанный канал (telegram или email).
    При неудаче логирует ошибку, но не поднимает исключение (non-blocking).
    """
    logger.info(
        "NotificationsCenter: канал=%s получатель=%s", req.channel, req.recipient
    )
    success = False

    if req.channel == "telegram":
        success = await _send_telegram(req.recipient, req.message)
    elif req.channel == "email":
        subject = "Уведомление от HR Screening Helper"
        success = await _send_email(req.recipient, subject, req.message)
    else:
        raise HTTPException(status_code=422, detail=f"Неизвестный канал уведомления: {req.channel}")

    if not success:
        logger.warning(
            "Уведомление не доставлено (канал=%s, получатель=%s). "
            "Проверьте учётные данные и доступность сервиса.",
            req.channel, req.recipient
        )

    return {
        "status": "отправлено" if success else "ошибка",
        "channel": req.channel,
        "recipient": req.recipient,
    }


@app.get("/health", tags=["служебные"])
async def health():
    """Проверка работоспособности NotificationsCenter."""
    return {"status": "ok", "service": "notifications_center"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8007, reload=True)
