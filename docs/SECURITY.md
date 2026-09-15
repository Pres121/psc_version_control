# Security model

PSC Update Hub is designed so **clients never hold privileged keys**.

## Trust boundaries

| Layer | What it can do |
|-------|----------------|
| Flutter apps | Call public endpoints only (`/updates/check`, `/announcements/check`, `/downloads/...`, device register) |
| Admin dashboard | Holds a short-lived JWT only; talks to FastAPI, never Supabase |
| FastAPI (Render) | Holds `SUPABASE_KEY` (service_role) + `SECRET_KEY` |
| Supabase | RLS enabled on all tables; storage bucket `app-builds` is private |

## Public vs protected

**Public (rate-limited):**
- `POST /api/v1/updates/check`
- `POST /api/v1/announcements/check`
- `GET /api/v1/downloads/{app_key}`
- `GET /download/{app_key}` (HTML)
- `POST /api/v1/notifications/devices/register`
- `POST /api/v1/auth/login` (strict rate limit)

**Admin JWT required:** apps, releases, uploads, publish, notifications send, logs, announcements create

## Required production settings (Render)

```
ENVIRONMENT=production
DOCS_ENABLED=false
SECRET_KEY=<32+ char random>
SUPABASE_URL=...
SUPABASE_KEY=<service_role>
ALLOWED_ORIGINS=["https://YOUR_ADMIN_ORIGIN"]
PUBLIC_BASE_URL=https://psc-version-control.onrender.com
STORAGE_BUCKET=app-builds
```

Generate `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Database / storage

Run migrations through `007_security_hardening.sql`:
- RLS on all app tables (no anon policies)
- `app-builds` bucket forced `public = false`
- accidental public storage policies dropped if present

Downloads use **short-lived signed URLs** created by the backend.

## Checklist after deploy

1. `/docs` returns 404 when `DOCS_ENABLED=false`
2. Admin login works; wrong password is rate-limited after repeated tries
3. Anon Supabase key cannot `select * from apps` or list `app-builds`
4. Upload APK as admin → Update Now opens download page → file downloads
5. CORS rejects unknown browser origins in production
