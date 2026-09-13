from unittest.mock import patch

from fastapi.testclient import TestClient
from pwdlib import PasswordHash

from app.main import app, limiter, settings
from app.services.email import TEMPLATE_DIR, render_email

client = TestClient(app)
settings.admin_password_hash = PasswordHash.recommended().hash("correct-password")
settings.qredit_platform_guide_url = "https://guide.test/platform.pdf"
settings.qredit_integration_documentation_url = "https://guide.test/integration.pdf"
settings.qredit_hero_image_url = "https://cdn.test/hero.jpg"
settings.require_admin_auth = True
settings.send_html_email = False
settings.qredit_platform_icon_url = "https://cdn.test/platform.png"
settings.qredit_integration_icon_url = "https://cdn.test/integration.png"
settings.qredit_support_icon_url = "https://cdn.test/support.png"


def login() -> None:
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "correct-password"})
    assert response.status_code == 200


def email_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "recipient_email": "person@example.com",
        "recipient_name": "Pat",
        "business_name": "Acme",
        "platform_username": "pat.acme",
        "platform_password": "temporary-password",
        "subject": "Hello",
        "recipient_agreed": True,
    }
    payload.update(overrides)
    return payload


def test_authentication() -> None:
    assert client.post("/api/auth/login", json={"email": "admin@example.com", "password": "wrong"}).status_code == 401
    login()
    assert client.get("/api/auth/me").status_code == 200


def test_send_requires_auth_and_validates_input() -> None:
    client.post("/api/auth/logout")
    payload = email_payload()
    assert client.post("/api/emails/send", json=payload).status_code == 401
    login()
    assert client.post("/api/emails/send", json={**payload, "recipient_email": "bad"}).status_code == 422
    assert client.post("/api/emails/send", json={**payload, "subject": "Hi\nBcc: bad@example.com"}).status_code == 422
    assert client.post("/api/emails/send", json={**payload, "recipient_agreed": False}).status_code == 400


def test_send_success_and_smtp_failure() -> None:
    login()
    payload = email_payload()
    with patch("app.services.email.smtplib.SMTP") as smtp:
        assert client.post("/api/emails/send", json=payload).status_code == 200
        smtp.return_value.__enter__.return_value.send_message.assert_called_once()
    limiter.attempts.clear()
    with patch("app.services.email.smtplib.SMTP", side_effect=OSError):
        assert client.post("/api/emails/send", json=payload).status_code == 502


def test_send_defaults_to_plain_text_only() -> None:
    login()
    payload = email_payload()
    with patch("app.services.email.smtplib.SMTP") as smtp:
        assert client.post("/api/emails/send", json=payload).status_code == 200
        message = smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
        raw_message = message.as_string()
        assert "Content-Type: text/plain" in raw_message
        assert message["X-Entity-Ref-ID"]
        assert "Content-Type: text/html" not in raw_message
        assert "Content-ID: <qredit-" not in raw_message
        assert "cid:qredit-" not in raw_message
        assert "Content-Disposition: attachment" not in raw_message
        assert "List-Unsubscribe" not in raw_message
        assert "List-Unsubscribe-Post" not in raw_message


def test_send_can_include_image_html_without_attachments() -> None:
    login()
    settings.send_html_email = True
    payload = email_payload()
    with patch("app.services.email.smtplib.SMTP") as smtp:
        assert client.post("/api/emails/send", json=payload).status_code == 200
        message = smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
        raw_message = message.as_string()
        html_part = message.get_payload()[1].get_content()
        assert "Content-Type: text/html" in raw_message
        assert "Content-ID: <qredit-" not in raw_message
        assert "cid:qredit-" not in raw_message
        assert "Content-Disposition: attachment" not in raw_message
        assert "<img" in html_part
        assert "<svg" not in html_part
        assert settings.qredit_hero_image_url in html_part
    settings.send_html_email = False


def test_rate_limit() -> None:
    login()
    limiter.attempts.clear()
    payload = email_payload()
    with patch("app.services.email.smtplib.SMTP"):
        for _ in range(10):
            assert client.post("/api/emails/send", json=payload).status_code == 200
        assert client.post("/api/emails/send", json=payload).status_code == 429


def test_qredit_template_personalization_links_and_safety() -> None:
    payload = email_payload(recipient_email="alex@example.com", recipient_name="A<lex", business_name="R&D <Partners>", platform_username="alex.user", platform_password="safe-pass", subject="Welcome")
    from app.models.schemas import EmailSendRequest
    plain_text, html = render_email(EmailSendRequest(**payload), settings)
    assert "Dear A<lex," in plain_text
    assert "R&D <Partners>" in plain_text
    assert "Username: alex.user" in plain_text
    assert "Password: safe-pass" in plain_text
    assert "https://guide.test/platform.pdf" in plain_text
    assert "https://guide.test/integration.pdf" in plain_text
    assert "A&lt;lex" in html
    assert "R&amp;D &lt;Partners&gt;" in html
    assert "alex.user" in html
    assert "safe-pass" in html
    assert "alex@example.com" in html
    assert "<img" in html
    assert "<svg" not in html
    for url in (settings.qredit_hero_image_url, settings.qredit_platform_icon_url, settings.qredit_integration_icon_url, settings.qredit_support_icon_url):
        assert url in html
    assert settings.qredit_platform_guide_url in html
    assert settings.qredit_integration_documentation_url in html
    assert settings.gmail_app_password not in html
    assert "smtp.gmail.com" not in html
    assert "qredit-email-hero" not in html
    assert "Download Platform Guide" in html
    assert "Download Integration Guide" in html
    assert (TEMPLATE_DIR / "qredit_welcome_email.html").exists()
    template_source = (TEMPLATE_DIR / "qredit_welcome_email.html").read_text(encoding="utf-8")
    assert "<img" in template_source
    assert "<svg" not in template_source
    assert "{{ hero_image_url }}" in template_source
    assert "{{ platform_icon_url }}" in template_source
    assert "{{ integration_icon_url }}" in template_source
    assert "{{ support_icon_url }}" in template_source
    assert "{{ t." in template_source
    assert (TEMPLATE_DIR / "qredit_welcome_translations.py").exists()
    assert not (TEMPLATE_DIR / "qredit_welcome_email_ar.html").exists()


def test_arabic_translation_is_selected_in_single_template() -> None:
    from app.models.schemas import EmailSendRequest
    payload = EmailSendRequest(
        recipient_email="ar@example.com",
        recipient_name="ليان",
        business_name="شركة",
        platform_username="ar.user",
        platform_password="ar-pass",
        subject="ترحيب",
        recipient_agreed=True,
        language="ar",
    )
    _, html = render_email(payload, settings)
    assert 'lang="ar"' in html
    assert "مرحباً" in html
    assert "ليان" in html
    assert "شركة" in html
    assert "Ù" not in html
    assert "Ø" not in html


def test_local_mode_allows_form_without_login() -> None:
    settings.require_admin_auth = False
    limiter.attempts.clear()
    payload = email_payload()
    with patch("app.services.email.smtplib.SMTP"):
        assert client.get("/api/auth/me").status_code == 200
        assert client.post("/api/emails/send", json=payload).status_code == 200
    settings.require_admin_auth = True

