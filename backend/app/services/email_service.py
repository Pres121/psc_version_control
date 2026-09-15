"""
Outbound email via Resend HTTP API.
API key must come from RESEND_API_KEY env — never hard-code secrets.
"""
from __future__ import annotations

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings


def send_email(*, to: str, subject: str, html: str, text: str | None = None) -> None:
    settings = get_settings()
    if not settings.RESEND_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email delivery is not configured (RESEND_API_KEY missing)",
        )

    payload: dict = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20.0,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to reach email provider",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send email",
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
