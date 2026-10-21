"""
Сервис FeedbackGenerator (FG) — генерация персонализированного текста обратной связи.

Использует Jinja2-шаблоны для формирования письма кандидату на основании решения ЛПР.
"""
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from jinja2 import Environment, BaseLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FeedbackGenerator Service",
    version="1.0.0",
    description=(
        "Сервис генерации обратной связи. "
        "Формирует персонализированный текст приглашения или мотивированного отказа для кандидата."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Jinja2-шаблоны писем обратной связи ──────────────────────────────────────

# Шаблон письма при положительном решении ЛПР (приглашение на второй этап)
APPROVED_TEMPLATE = """Уважаемый(ая) {{ candidate_name }}!

Благодарим вас за участие в автоматизированном скрининге.

Мы рады сообщить, что по результатам оценки (AI: {{ ai_score }}/10, HR: {{ hr_score }}/10) \
вы приглашаетесь на второй этап отбора.

{% if hr_comment %}
Комментарий HR-специалиста: {{ hr_comment }}
{% endif %}

Наш сотрудник свяжется с вами для согласования времени следующего интервью.

С уважением,
HR-команда"""

# Шаблон письма при отрицательном решении ЛПР (отказ по скринингу)
REJECTED_TEMPLATE = """Уважаемый(ая) {{ candidate_name }}!

Благодарим вас за интерес к нашей компании и участие в скрининге.

К сожалению, по итогам оценки вашей кандидатуры мы вынуждены сообщить, \
что на данный момент не готовы продолжить рассмотрение вашей заявки.

{% if hr_comment %}
Комментарий: {{ hr_comment }}
{% endif %}

Мы сохраним ваше резюме в нашей базе и, возможно, вернёмся к вашей кандидатуре \
при появлении подходящих вакансий.

С уважением,
HR-команда"""

# Инициализируем Jinja2-окружение с загрузчиком из строки
_jinja_env = Environment(loader=BaseLoader())


class FeedbackRequest(BaseModel):
    """Тело запроса генерации обратной связи."""
    candidate_name: str
    decision: str           # 'approved' (приглашение) | 'rejected' (отказ)
    hr_comment: Optional[str] = None
    ai_score: Optional[float] = 0.0
    hr_score: Optional[float] = 0.0


@app.post("/generate", summary="Сгенерировать текст обратной связи")
async def generate_feedback(req: FeedbackRequest):
    """
    Генерирует персонализированный текст обратной связи на основании решения ЛПР.

    - decision='approved' → письмо с приглашением на второй этап
    - decision='rejected' → письмо с мотивированным отказом
    """
    logger.info(
        "FeedbackGenerator: кандидат=%s решение=%s", req.candidate_name, req.decision
    )

    # Выбираем шаблон в зависимости от решения ЛПР
    template_str = APPROVED_TEMPLATE if req.decision == "approved" else REJECTED_TEMPLATE
    template = _jinja_env.from_string(template_str)

    feedback_text = template.render(
        candidate_name=req.candidate_name,
        hr_comment=req.hr_comment or "",
        ai_score=f"{req.ai_score:.1f}" if req.ai_score is not None else "—",
        hr_score=f"{req.hr_score:.1f}" if req.hr_score is not None else "—",
    )

    return {"feedback_text": feedback_text}


@app.get("/health", tags=["служебные"])
async def health():
    """Проверка работоспособности сервиса FeedbackGenerator."""
    return {"status": "ok", "service": "feedback_generator"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8006, reload=True)
