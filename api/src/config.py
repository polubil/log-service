from functools import lru_cache
from typing import Self
from dotenv import find_dotenv
from urllib.parse import quote_plus


from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str | None = None
    db_name: str | None = None
    db_user: str | None = None
    db_password: SecretStr | None = None
    db_host: str | None = None
    db_port: int | None = None

    model_config = SettingsConfigDict(
        env_file=find_dotenv(".env.dev"),
        extra="ignore",
    )

    @model_validator(mode="after")
    def build_database_url(self) -> Self:
        if self.database_url:
            return self

        creds = [
            self.db_host,
            self.db_name,
            self.db_port,
            self.db_user,
            self.db_password,
        ]

        if not any(creds):
            raise ValueError("Set DATABASE_URL or full DB_* credentials")

        if not all(creds):
            raise ValueError(
                "DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD must be set together"
            )

        password = quote_plus(self.db_password.get_secret_value())
        self.database_url = (
            f"postgresql://{self.db_user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()
