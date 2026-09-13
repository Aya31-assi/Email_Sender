import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def reject_header_injection(value: str) -> str:
    if "\r" in value or "\n" in value:
        raise ValueError("Newline characters are not allowed")
    return value.strip()


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class EmailSendRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    recipient_email: EmailStr
    recipient_name: str = Field(min_length=1, max_length=120)
    business_name: str = Field(min_length=1, max_length=160)
    platform_username: str = Field(min_length=1, max_length=160)
    platform_password: str = Field(min_length=1, max_length=160)
    subject: str = Field(min_length=1, max_length=200)
    recipient_agreed: bool
    language: str = "en"

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        if value not in {"en", "ar"}:
            raise ValueError("Language must be en or ar")
        return value

    @field_validator("recipient_email", "recipient_name", "business_name", "platform_username", "platform_password", "subject", mode="before")
    @classmethod
    def validate_headers(cls, value: str) -> str:
        return reject_header_injection(value)

    @field_validator("recipient_name", "business_name", "platform_username", "platform_password", "subject")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", value):
            raise ValueError("Unsupported control characters")
        return value


class UserResponse(BaseModel):
    email: EmailStr
