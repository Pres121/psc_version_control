"""
One-time helper: open Google OAuth consent and print a Gmail refresh token.

Prerequisites:
  - Gmail API enabled in Google Cloud
  - OAuth Web client with redirect URI: http://localhost:8765/
  - If OAuth app is in Testing: add the Gmail account as a Test user

Usage (from backend/):
  set GMAIL_CLIENT_ID=...
  set GMAIL_CLIENT_SECRET=...
  python scripts/get_gmail_refresh_token.py

Sign in as the mailbox that will send OTP emails (e.g. pscecosystem@gmail.com).
"""
from __future__ import annotations

import os
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx

REDIRECT_URI = "http://localhost:8765/"
SCOPE = "https://www.googleapis.com/auth/gmail.send"
PORT = 8765


def main() -> int:
    client_id = os.environ.get("GMAIL_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        print("Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in the environment first.")
        return 1

    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    result: dict[str, str] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            if "code" in qs:
                result["code"] = qs["code"][0]
                body = b"<html><body><h2>OK - you can close this tab.</h2></body></html>"
                self.send_response(200)
            else:
                err = qs.get("error", ["unknown"])[0]
                result["error"] = err
                body = f"<html><body><h2>Error: {err}</h2></body></html>".encode()
                self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):  # noqa: A003
            return

    print("Opening browser for Google consent…")
    print("If it does not open, visit:\n", auth_url, "\n")
    webbrowser.open(auth_url)

    server = HTTPServer(("127.0.0.1", PORT), Handler)
    while "code" not in result and "error" not in result:
        server.handle_request()
    server.server_close()

    if "error" in result:
        print("OAuth failed:", result["error"])
        return 1

    token_resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": result["code"],
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=30.0,
    )
    if token_resp.status_code >= 400:
        print("Token exchange failed:", token_resp.status_code, token_resp.text)
        return 1

    data = token_resp.json()
    refresh = data.get("refresh_token")
    if not refresh:
        print(
            "No refresh_token returned. Revoke prior access at "
            "https://myaccount.google.com/permissions then run again with prompt=consent."
        )
        print("Response keys:", list(data.keys()))
        return 1

    print("\n=== Add this to Render (and local .env) ===\n")
    print(f"GMAIL_REFRESH_TOKEN={refresh}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
