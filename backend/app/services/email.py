import logging
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime, formataddr, make_msgid
from pathlib import Path
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from app.core.config import Settings
from app.models.schemas import EmailSendRequest
from app.templates.qredit_welcome_translations import get_translation

logger = logging.getLogger(__name__)
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=select_autoescape(["html", "xml"]), undefined=StrictUndefined)


def render_email(payload: EmailSendRequest, settings: Settings) -> tuple[str, str]:
    translation = get_translation(payload.language)
    template = environment.get_template("qredit_welcome_email.html")
    html = template.render(
        t=translation,
        is_rtl=translation["dir"] == "rtl",
        first_name=payload.recipient_name,
        business_name=payload.business_name,
        platform_username=payload.platform_username,
        platform_password=payload.platform_password,
        recipient_email=str(payload.recipient_email),
        hero_image_url=settings.qredit_hero_image_url,
        platform_icon_url=settings.qredit_platform_icon_url,
        integration_icon_url=settings.qredit_integration_icon_url,
        support_icon_url=settings.qredit_support_icon_url,
        platform_guide_url=settings.qredit_platform_guide_url,
        integration_documentation_url=settings.qredit_integration_documentation_url,
    )
    html = html.lstrip("\ufeff")
    text = translation["plain_text"].format(
        recipient_name=payload.recipient_name,
        business_name=payload.business_name,
        platform_username=payload.platform_username,
        platform_password=payload.platform_password,
        platform_guide_url=settings.qredit_platform_guide_url,
        integration_documentation_url=settings.qredit_integration_documentation_url,
    )
    return text, html


def send_email(payload: EmailSendRequest, settings: Settings) -> None:
    text, html = render_email(payload, settings)
    message = EmailMessage()
    message["From"] = formataddr(("Qredit Team", settings.from_email))
    message["To"] = str(payload.recipient_email)
    message["Subject"] = payload.subject
    message["Date"] = format_datetime(datetime.now(timezone.utc))
    message["Message-ID"] = make_msgid()
    message["X-Entity-Ref-ID"] = str(uuid4())
    message["Reply-To"] = settings.from_email
    message.set_content(text)
    if settings.send_html_email:
        message.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(settings.gmail_email, settings.gmail_app_password)
            smtp.send_message(message)
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed while sending an email")
        raise
    except (smtplib.SMTPException, OSError):
        logger.exception("SMTP delivery failed")
        raise
    logger.info("Email sent successfully to recipient")
