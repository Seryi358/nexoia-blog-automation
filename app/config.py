from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str

    # KIE AI (Nano Banana 2 for images)
    kie_api_key: str
    kie_base_url: str = "https://api.kie.ai/api/v1"

    # WordPress REST API
    wp_url: str  # e.g. https://nexoia.com
    wp_user: str  # WordPress username
    wp_app_password: str  # WordPress Application Password

    # Scheduler
    publish_days: str = "mon,wed,fri"
    publish_hour: int = 9
    publish_minute: int = 0
    timezone: str = "America/Bogota"

    # Content
    articles_per_batch: int = 1
    min_word_count: int = 1800
    max_word_count: int = 2500
    language: str = "es"

    # App
    app_port: int = 8001
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
