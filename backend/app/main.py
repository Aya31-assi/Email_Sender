import logging
import smtplib

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.models.schemas import EmailSendRequest, LoginRequest, UserResponse
from app.services.auth import COOKIE_NAME, authenticated_email, create_token, verify_admin
from app.services.email import send_email
from app.services.rate_limit import SendRateLimiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()
limiter = SendRateLimiter()
app = FastAPI(title="Northstar Email Sender")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url], allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response) -> UserResponse:
    if not verify_admin(str(payload.email), payload.password, settings):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    response.set_cookie(COOKIE_NAME, create_token(str(payload.email), settings), httponly=True, secure=settings.cookie_secure, samesite="strict", max_age=1800)
    return UserResponse(email=payload.email)


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, secure=settings.cookie_secure, httponly=True, samesite="strict")


@app.get("/api/auth/me", response_model=UserResponse)
def me(request: Request) -> UserResponse:
    email = authenticated_email(request, settings)
    if not settings.require_admin_auth:
        return UserResponse(email=settings.admin_email)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return UserResponse(email=email)


@app.post("/api/emails/send")
def send(payload: EmailSendRequest, request: Request) -> dict[str, str]:
    email = authenticated_email(request, settings)
    if settings.require_admin_auth and not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    email = email or settings.admin_email
    if not payload.recipient_agreed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipient consent is required")
    if not limiter.allow(email):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Send limit reached")
    try:
        send_email(payload, settings)
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Gmail rejected the configured app password or account settings.") from None
    except smtplib.SMTPRecipientsRefused:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Gmail refused the recipient address.") from None
    except smtplib.SMTPSenderRefused:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Gmail refused the configured sender address.") from None
    except smtplib.SMTPDataError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Gmail rejected the email content.") from None
    except (smtplib.SMTPException, OSError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to reach Gmail SMTP. Check the network connection and Gmail SMTP availability.") from None
    except Exception:
        logger.exception("Unexpected email send failure")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to send email") from None
    return {"message": "Email sent successfully"}
