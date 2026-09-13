from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    email_provider: str = "gmail"
    from_email: str = Field(min_length=3)
    gmail_email: str = Field(min_length=3)
    gmail_app_password: str = Field(min_length=1)
    admin_email: str = Field(min_length=3)
    admin_password_hash: str = Field(min_length=10)
    jwt_secret: str = Field(min_length=32)
    frontend_url: str = "http://localhost:5173"
    cookie_secure: bool = False
    environment: str = "development"
    require_admin_auth: bool = True
    send_html_email: bool = False
    qredit_platform_guide_url: str = Field(min_length=1)
    qredit_integration_documentation_url: str = Field(min_length=1)
    qredit_hero_image_url: str = Field(min_length=1)
    qredit_platform_icon_url: str = Field(min_length=1)
    qredit_integration_icon_url: str = Field(min_length=1)
    qredit_support_icon_url: str = Field(min_length=1)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("gmail_app_password", mode="before")
    @classmethod
    def remove_app_password_spaces(cls, value: str) -> str:
        return value.replace(" ", "")

    @field_validator(
        "qredit_platform_guide_url",
        "qredit_integration_documentation_url",
        "qredit_hero_image_url",
        "qredit_platform_icon_url",
        "qredit_integration_icon_url",
        "qredit_support_icon_url",
    )
    @classmethod
    def require_https_url(cls, value: str) -> str:
        if not value or not value.startswith("https://"):
            raise ValueError("Qredit URLs must be non-empty HTTPS URLs")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
