import logging
import httpx
from ..config import settings

logger = logging.getLogger(__name__)


class NotificationsClient:
    """
    HTTP-клиент к микросервису NotificationsCenter (NotC).
    Отправляет уведомления HR-специалисту, ЛПР и кандидатам через Email или Telegram.
    """

    async def notify(
        self,
        recipient: str,
        message: str,
        channel: str = "email",
    ) -> bool:
        """
        Отправить уведомление через указанный канал.

        Args:
            recipient: адрес получателя (email / Telegram chat_id) или ключевое слово 'hr'/'lpr'
            message: текст уведомления
            channel: 'email' или 'telegram'

        Returns:
            True при успешной отправке, False при ошибке.
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{settings.notifications_center_url}/notify",
                    json={"recipient": recipient, "message": message, "channel": channel},
                )
                resp.raise_for_status()
                return True
        except Exception as exc:
            logger.warning("NotificationsClient: ошибка отправки уведомления: %s", exc)
            return False
