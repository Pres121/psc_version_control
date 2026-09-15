"""
Outbound email via Gmail API (OAuth2 refresh token).
Credentials come from env — never hard-code secrets.
"""
from __future__ import annotations

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"


def _gmail_configured(settings) -> bool:
    return bool(
        settings.GMAIL_CLIENT_ID
        and settings.GMAIL_CLIENT_SECRET
        and settings.GMAIL_REFRESH_TOKEN
        and settings.GMAIL_SENDER_EMAIL
    )


def _access_token(settings) -> str:
    try:
        response = httpx.post(
            _TOKEN_URL,
            data={
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "refresh_token": settings.GMAIL_REFRESH_TOKEN,
                "grant_type": "refresh_token",
            },
            timeout=20.0,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to reach Google OAuth token endpoint",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to refresh Gmail access token",
        )

    token = response.json().get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gmail access token missing from OAuth response",
        )
    return token


def _build_raw_message(*, to: str, subject: str, html: str, text: str | None, sender: str) -> str:
    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["From"] = sender
    msg["Subject"] = subject
    if text:
        msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii").rstrip("=")
    return raw


def send_email(*, to: str, subject: str, html: str, text: str | None = None) -> None:
    settings = get_settings()
    if not _gmail_configured(settings):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email delivery is not configured (Gmail OAuth env vars missing)",
        )

    token = _access_token(settings)
    raw = _build_raw_message(
        to=to,
        subject=subject,
        html=html,
        text=text,
        sender=settings.GMAIL_SENDER_EMAIL,
    )

    try:
        response = httpx.post(
            _GMAIL_SEND_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"raw": raw},
            timeout=20.0,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to reach Gmail API",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send email via Gmail",
        )


def send_otp_email(*, to: str, code: str, full_name: str | None = None) -> None:
    settings = get_settings()
    greeting = f"Hi {full_name}," if full_name else "Hi,"
    minutes = settings.OTP_EXPIRE_MINUTES
    html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.5;color:#0b1220">
      <p>{greeting}</p>
      <p>Your PSC Update Hub verification code is:</p>
      <p style="font-size:28px;font-weight:700;letter-spacing:6px;margin:16px 0">{code}</p>
      <p>This code expires in {minutes} minutes. If you did not try to sign in, you can ignore this email.</p>
      <p style="color:#6b7a90;font-size:12px">PSC Update Hub</p>
    </div>
    """
    text = f"{greeting}\n\nYour PSC Update Hub verification code is: {code}\nExpires in {minutes} minutes."
    send_email(to=to, subject=f"Your PSC login code: {code}", html=html, text=text)


def send_admin_invite_email(
    *,
    to: str,
    full_name: str | None,
    temporary_password: str,
    role: str,
) -> None:
    settings = get_settings()
    greeting = f"Hi {full_name}," if full_name else "Hi,"
    dashboard = settings.PUBLIC_BASE_URL.rstrip("/")
    html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.5;color:#0b1220">
      <p>{greeting}</p>
      <p>You have been added as a <strong>{role}</strong> on PSC Update Hub.</p>
      <p><strong>Email:</strong> {to}<br/>
      <strong>Temporary password:</strong> {temporary_password}</p>
      <p>Sign in, complete OTP verification, then change your password with your administrator if needed.</p>
      <p style="color:#6b7a90;font-size:12px">PSC Update Hub · {dashboard}</p>
    </div>
    """
    text = (
        f"{greeting}\n\nYou were added as {role} on PSC Update Hub.\n"
        f"Email: {to}\nTemporary password: {temporary_password}\n"
    )
    send_email(to=to, subject="Your PSC Update Hub admin account", html=html, text=text)
