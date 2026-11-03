"""
Клиент для взаимодействия со шлюзом API Gateway (FastAPI).
Обеспечивает отправку HTTP-запросов и обработку ответов от бэкенда.
"""
import base64
import os
import requests
from typing import Optional, Tuple, Any

DEFAULT_GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000").rstrip("/")


class APIClient:
    def __init__(self, base_url: str = DEFAULT_GATEWAY_URL):
        self.base_url = base_url.rstrip("/")

    # ── Служебные ─────────────────────────────────────────────────────────────

    def check_health(self) -> Tuple[bool, str]:
        """Проверка связи с API Gateway."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            if resp.status_code == 200:
                return True, "API Gateway доступен и работает"
            return False, f"Ошибка статуса: {resp.status_code}"
        except Exception as e:
            return False, f"Не удалось подключиться к {self.base_url}: {e}"

    # ── Контур Кандидата ──────────────────────────────────────────────────────

    def get_candidate_session(self, token: str) -> Tuple[Optional[dict], Optional[str]]:
        """Вход по токен-ссылке кандидата."""
        try:
            resp = requests.get(f"{self.base_url}/api/v1/session/{token}", timeout=10)
            if resp.status_code == 200:
                return resp.json(), None
            detail = resp.json().get("detail", resp.text)
            return None, f"Ошибка {resp.status_code}: {detail}"
        except Exception as e:
            return None, f"Сетевая ошибка: {e}"

    def submit_pdn(self, token: str, accept_pdn: bool) -> Tuple[Optional[dict], Optional[str]]:
        """Фиксация согласия или отказа от обработки ПДн (152-ФЗ)."""
        try:
            resp = requests.post(
                f"{self.base_url}/api/v1/session/{token}/pdn",
                json={"accept_pdn": accept_pdn},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json(), None
            detail = resp.json().get("detail", resp.text)
            return None, f"Ошибка {resp.status_code}: {detail}"
        except Exception as e:
            return None, f"Сетевая ошибка: {e}"

    def get_next_question(self, token: str) -> Tuple[Optional[dict], Optional[str]]:
        """Получение очередного вопроса скрининга с аудио (TTS)."""
        try:
            resp = requests.get(f"{self.base_url}/api/v1/session/{token}/question", timeout=15)
            if resp.status_code == 200:
                return resp.json(), None
            detail = resp.json().get("detail", resp.text)
            return None, f"Ошибка {resp.status_code}: {detail}"
        except Exception as e:
            return None, f"Сетевая ошибка: {e}"

    def submit_answer(
        self, token: str, question_id: int, audio_bytes: bytes, filename: str = "answer.wav"
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Загрузка голосового ответа кандидата (multipart/form-data)."""
        try:
            files = {"audio": (filename, audio_bytes, "audio/wav")}
            data = {"question_id": question_id}
            resp = requests.post(
                f"{self.base_url}/api/v1/session/{token}/answer",
                data=data,
                files=files,
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json(), None
            detail = resp.json().get("detail", resp.text)
            return None, f"Ошибка {resp.status_code}: {detail}"
        except Exception as e:
            return None, f"Сетевая ошибка: {e}"

    def finish_session(self, token: str) -> Tuple[Optional[dict], Optional[str]]:
        """Завершение сессии скрининга: запуск ИИ-оценки и прощальная реплика."""
        try:
            resp = requests.post(f"{self.base_url}/api/v1/session/{token}/finish", timeout=60)
            if resp.status_code == 200:
                return resp.json(), None
            detail = resp.json().get("detail", resp.text)
            return None, f"Ошибка {resp.status_code}: {detail}"
        except Exception as e:
            return None, f"Сетевая ошибка: {e}"

    # ── Контур HR-специалиста и ЛПР ───────────────────────────────────────────

    def get_all_responses(self) -> Tuple[list, Optional[str]]:
        """Получить список всех откликов."""
        try:
            resp = requests.get(f"{self.base_url}/api/v1/screening/responses", timeout=10)
            if resp.status_code == 200:
                return resp.json(), None
            return [], f"Ошибка {resp.status_code}: {resp.text}"
        except Exception as e:
            return [], f"Сетевая ошибка: {e}"

    def get_transcript(self, response_id: int) -> Tuple[Optional[dict], Optional[str]]:
        """Получение транскрипта ответов кандидата (без оценки ИИ — слепое оценивание)."""
        try:
            resp = requests.get(f"{self.base_url}/api/v1/screening/{response_id}/transcript", timeout=10)
            if resp.status_code == 200:
                return resp.json(), None
            detail = resp.json().get("detail", resp.text)
            return None, f"Ошибка {resp.status_code}: {detail}"
        except Exception as e:
            return None, f"Сетевая ошибка: {e}"

    def submit_hr_review(
        self, response_id: int, hr_score: float, hr_comment: str
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Сохранение независимой оценки HR-специалиста."""
        try:
            resp = requests.post(
                f"{self.base_url}/api/v1/screening/{response_id}/hr-review",
                json={"hr_score": hr_score, "hr_comment": hr_comment},
                timeout=20,
            )
            if resp.status_code == 200:
                return resp.json(), None
            detail = resp.json().get("detail", resp.text)
            return None, f"Ошибка {resp.status_code}: {detail}"
        except Exception as e:
            return None, f"Сетевая ошибка: {e}"

    def get_full_result(self, response_id: int) -> Tuple[Optional[dict], Optional[str]]:
        """Получение полного результата (отклик + оценки AI и HR) для ЛПР."""
        try:
            resp = requests.get(f"{self.base_url}/api/v1/screening/{response_id}/result", timeout=10)
            if resp.status_code == 200:
                return resp.json(), None
            detail = resp.json().get("detail", resp.text)
            return None, f"Ошибка {resp.status_code}: {detail}"
        except Exception as e:
            return None, f"Сетевая ошибка: {e}"

    def download_report(self, response_id: int) -> Tuple[Optional[bytes], Optional[str]]:
        """Скачивание сгенерированного .docx-отчёта."""
        try:
            resp = requests.get(f"{self.base_url}/api/v1/screening/{response_id}/report", timeout=15)
            if resp.status_code == 200:
                return resp.content, None
            detail = resp.text
            return None, f"Ошибка {resp.status_code}: {detail}"
        except Exception as e:
            return None, f"Сетевая ошибка: {e}"

    def submit_lpr_decision(
        self, response_id: int, decision: str
    ) -> Tuple[Optional[dict], Optional[str]]:
        """Фиксация решения ЛПР ('approved' / 'rejected')."""
        try:
            resp = requests.post(
                f"{self.base_url}/api/v1/screening/{response_id}/decision",
                json={"decision": decision},
                timeout=20,
            )
            if resp.status_code == 200:
                return resp.json(), None
            detail = resp.json().get("detail", resp.text)
            return None, f"Ошибка {resp.status_code}: {detail}"
        except Exception as e:
            return None, f"Сетевая ошибка: {e}"

    # ── Демо / Тестирование ───────────────────────────────────────────────────

    def seed_demo_data(self) -> Tuple[Optional[dict], Optional[str]]:
        """Создание полного набора тестовых данных (Проект, Вакансия, Вопросы, Кандидат, Отклик)."""
        try:
            resp = requests.post(f"{self.base_url}/api/v1/screening/demo-seed", timeout=20)
            if resp.status_code in (200, 201):
                return resp.json(), None
            detail = resp.text
            return None, f"Ошибка {resp.status_code}: {detail}"
        except Exception as e:
            return None, f"Сетевая ошибка: {e}"


def decode_base64_audio(audio_base64: Optional[str]) -> Optional[bytes]:
    """Вспомогательная функция для декодирования аудио из base64."""
    if not audio_base64:
        return None
    try:
        return base64.b64decode(audio_base64)
    except Exception:
        return None
