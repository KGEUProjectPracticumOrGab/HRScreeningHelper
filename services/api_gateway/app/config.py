from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # URL-адреса внутренних микросервисов
    db_connector_url: str = "http://localhost:8001"
    tts_service_url: str = "http://localhost:8002"
    stt_service_url: str = "http://localhost:8003"
    llm_service_url: str = "http://localhost:8004"
    json_to_word_url: str = "http://localhost:8005"
    feedback_generator_url: str = "http://localhost:8006"
    notifications_center_url: str = "http://localhost:8007"

    # Настройки удалённого Colab AI-воркера (USE_COLAB_AI_WORKER=true/false)
    use_colab_ai_worker: bool = False
    colab_ai_url: str = "https://your-ngrok-url.ngrok-free.app"
    colab_tts_endpoint: str = "/tts"
    colab_stt_endpoint: str = "/stt"
    colab_llm_endpoint: str = "/llm"

    # Директория для хранения сгенерированных отчётов
    report_output_dir: str = "./reports"

    class Config:
        env_file = ".env"


settings = Settings()
