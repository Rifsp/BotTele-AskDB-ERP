from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://localhost:5432/postgres"
    openai_api_key: str = ""
    openai_base_url: str = "https://konektikacloud.web.id/v1"
    openai_model: str = "konektika-pro"
    app_name: str = "DB-Chat"
    debug: bool = True
    max_rows: int = 100
    query_timeout: int = 30
    telegram_bot_token: str = ""
    authorized_user_ids: str = ""

    @property
    def authorized_users(self) -> list[int]:
        if not self.authorized_user_ids:
            return []
        return [int(uid.strip()) for uid in self.authorized_user_ids.split(",") if uid.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
