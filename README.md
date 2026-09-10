# PSC — Centralized App Update Management System

A single backend that lets all PSC Flutter apps (PSC Notes, PSC
Calendar, PSC Savings, PSC Inventory, and any future PSC app) check
for updates, be forced onto a minimum supported version when needed,
and receive targeted push notifications — all managed from one admin
dashboard.

```
Flutter Apps  ──HTTPS/REST──▶  FastAPI Backend  ──▶  Supabase PostgreSQL
                                     ▲
Admin Dashboard  ──HTTPS/REST───────┘
```

No client (Flutter app or dashboard) ever holds Supabase or FCM
credentials — everything privileged happens behind FastAPI.

## Repository layout

```
psc-update-system/
├── backend/            FastAPI service (see backend/README below)
├── supabase/
│   └── migrations/001_init_schema.sql
├── flutter_package/
│   └── psc_update_service/   reusable Flutter package
├── admin_dashboard/    static HTML/JS/CSS admin UI
└── docs/               API.md, ARCHITECTURE.md
```

## Quick start

### 1. Database
Run these SQL migrations against your Supabase project (SQL Editor, or
`supabase db push` / psql), in order:

1. `supabase/migrations/001_init_schema.sql`
2. `supabase/migrations/002_make_release_update_url_optional.sql`
3. `supabase/migrations/003_request_logs.sql` — required for the **Logs** page

### 2. Backend
```bash
cd backend
cp .env.example .env        # fill in SUPABASE_URL, SUPABASE_KEY (service_role), SECRET_KEY, etc.
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Create your first admin user:
```bash
python -m scripts.create_admin you@psc.com "StrongPassword123" "Your Name" superadmin
```
Docs available at `http://localhost:8000/docs`.

### 3. Admin dashboard
`admin_dashboard/` is static HTML/JS — serve it with any static host
(or `python -m http.server` locally) and set `window.PSC_API_BASE` in
each page (or before `js/api.js` loads) to your backend URL. Open
`login.html` first.

### 4. Flutter apps
Add `psc_update_service` as a dependency (see
`flutter_package/psc_update_service/README.md`) to each of PSC Notes,
PSC Calendar, PSC Savings, and PSC Inventory. Two lines of integration
per app.

### 5. Deploy
`backend/render.yaml` + `backend/Dockerfile` deploy the API to Render.
Point Flutter apps and the dashboard at the deployed HTTPS URL.

## Adding a new PSC app (e.g. "PSC App 5")

No backend code changes needed:
1. Add it from the admin dashboard's **Applications** page (name,
   `app_key`, package name, platform).
2. Add `psc_update_service` to the new app with its own `app_key`.
3. Create and publish releases for it from the **Releases** page.

See `docs/ARCHITECTURE.md`, `docs/API.md`, and `docs/NOTIFICATIONS.md`
for more detail (including Flutter FCM snippets).
