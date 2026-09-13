# Qredit Email Sender

A small admin workspace for sending Qredit welcome and onboarding emails. The frontend is React + Vite + TypeScript, and the backend is FastAPI with Gmail SMTP delivery.

## Requirements

- Python 3.11+
- Node.js 20+
- A Gmail account with Google 2-Step Verification enabled
- Public HTTPS URLs for email images if HTML image rendering is enabled

## Backend Setup

PowerShell:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/generate_password_hash.py
```

Paste the generated hash into `ADMIN_PASSWORD_HASH` in `backend/.env`.

Generate a JWT secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Start FastAPI:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend Setup

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

The frontend runs at `http://localhost:5173` and calls the backend through `VITE_API_URL`.

## Environment

Important backend settings:

- `FROM_EMAIL` and `GMAIL_EMAIL`: the Gmail account used to send.
- `GMAIL_APP_PASSWORD`: Google App Password, not the normal Gmail password.
- `ADMIN_EMAIL` and `ADMIN_PASSWORD_HASH`: admin login credentials.
- `JWT_SECRET`: long random secret for login cookies.
- `REQUIRE_ADMIN_AUTH`: set `false` for local open access, `true` for login.
- `SEND_HTML_EMAIL`: set `true` to send the designed HTML email.
- `QREDIT_*_URL`: public HTTPS links for the hero image, icons, and PDF guides used inside the email template.

Email clients cannot load images from `localhost` or private files. Use public HTTPS URLs for `QREDIT_HERO_IMAGE_URL`, `QREDIT_PLATFORM_ICON_URL`, `QREDIT_INTEGRATION_ICON_URL`, and `QREDIT_SUPPORT_ICON_URL`.

The Arabic and English versions share one HTML template. Text lives in `backend/app/templates/qredit_welcome_translations.py`; layout lives in `backend/app/templates/qredit_welcome_email.html`.

## Checks

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Frontend:

```powershell
cd frontend
npm run build
```

## Security Notes

- Keep `backend/.env` private.
- Use `COOKIE_SECURE=true` behind HTTPS in production.
- Gmail SMTP does not guarantee inbox placement. SPF, DKIM, DMARC, sender reputation, content, and recipient behavior all affect Spam/Inbox placement.
- For production sending, consider a transactional email provider with domain authentication, bounce handling, and deliverability analytics.

## Project Structure

```text
email-sender/
  backend/
    app/core/       settings
    app/models/     Pydantic request models
    app/services/   auth, rate limiting, SMTP delivery
    app/templates/  Qredit HTML email template and translations
    scripts/        password hash utility
    tests/          mocked SMTP API tests
  frontend/
    src/            React app and API client
```
