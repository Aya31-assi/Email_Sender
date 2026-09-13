from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Request
from pwdlib import PasswordHash

from app.core.config import Settings

password_hash = PasswordHash.recommended()
COOKIE_NAME = "admin_session"
TOKEN_TTL_MINUTES = 30


def verify_admin(email: str, password: str, settings: Settings) -> bool:
    try:
        return email.casefold() == settings.admin_email.casefold() and password_hash.verify(password, settings.admin_password_hash)
    except Exception:
        return False


def create_token(email: str, settings: Settings) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)
    return jwt.encode({"sub": email, "exp": expires}, settings.jwt_secret, algorithm="HS256")


def authenticated_email(request: Request, settings: Settings) -> str | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        email = payload.get("sub")
        return email if isinstance(email, str) and email.casefold() == settings.admin_email.casefold() else None
    except jwt.PyJWTError:
        return None
