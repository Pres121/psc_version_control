# Architecture

> [!NOTE]
> For the comprehensive, formal Technical Team Documentation including Flutter app connectivity, microservice data flows, database schemas, and threat models, see [`TECHNICAL_DOCUMENTATION.md`](file:///c:/Users/user/Desktop/Personal_Projetcs/psc_version_control/docs/TECHNICAL_DOCUMENTATION.md).

## Overview

```
                 ┌───────────────────┐
                 │   Flutter Apps     │
                 │  Notes / Calendar  │
                 │  Savings / ...     │
                 └─────────┬──────────┘
                           │ HTTPS / REST
                           ▼
                 ┌───────────────────┐        ┌────────────────┐
                 │   FastAPI Backend  │◀──────▶│  Admin Dashboard│
                 │  (Render, Docker)  │  HTTPS  │  (static HTML)  │
                 └─────────┬──────────┘        └────────────────┘
                           │ service_role key (server-side only)
                           ▼
                 ┌───────────────────┐
                 │ Supabase PostgreSQL│
                 └───────────────────┘
```

## Why this shape

- **FastAPI as the only privileged writer.** Both the Flutter apps
  and the admin dashboard talk exclusively to FastAPI over REST. The
  Supabase service-role key lives only in the backend's environment
  variables — never in a mobile app bundle or browser bundle where it
  could be extracted.
- **RLS enabled, no anon policies.** Row Level Security is turned on
  for every table in `001_init_schema.sql`, but no policies are
  granted to `anon`/`authenticated` roles. This means even if a
  Supabase anon key leaked, it could read/write nothing — all access
  goes through the backend's service-role connection.
- **Registry pattern for apps, not hard-coding.** The `apps` table is
  the single source of truth for which PSC applications exist. Every
  other table (`releases`, `devices`, `notification_logs`) references
  `apps.id`. No route or service function is written against a
  specific app — `check_for_update()`, the releases API, and the
  notification service all operate generically on whatever `app_key`
  is passed in. This is what lets a 5th, 6th, 7th PSC app be added
  purely through data (an admin-dashboard form submission) instead of
  a code change.
- **Offline-first client design.** The Flutter package treats the
  update-check as a "nice to have" background call: short timeout,
  broad exception handling, and a `SharedPreferences` cache of the
  last successful result. A network failure never prevents the host
  app from opening or functioning.
- **Semantic version comparison, not string comparison.** Comparing
  `"1.10.0"` and `"1.9.0"` as strings gives the wrong answer
  (`"1.10.0" < "1.9.0"` lexically). `app/services/version_service.py`
  parses each version into `(major, minor, patch, pre-release)` and
  compares numerically, which is what both the update-check endpoint
  and the mandatory-update logic rely on.
- **Mandatory vs. optional updates are two independent comparisons.**
  `update_available` = latest published version > installed version.
  `update_required` = installed version < release's
  `minimum_supported_version`. A release can raise the minimum
  supported version independently of its own version number, so PSC
  can ship an optional 1.9.0 today and later mark 1.7.0 as the new
  floor without publishing a new release.
- **Per-app FCM topics, not per-device fan-out logic in the backend.**
  Each app's Flutter integration subscribes its device to a topic
  named after its own `app_key`. The backend just publishes to that
  topic when a release notification is sent, so PSC Notes updates can
  never reach PSC Calendar's users, and no per-device targeting logic
  needs to live in FastAPI.
- **Duplicate-notification protection at the DB layer.** A unique
  constraint on `notification_logs.release_id` means a race condition
  or double-click on "Send Notification" cannot result in the same
  release notifying users twice — the second insert simply fails.

## Data model

| Table | Purpose |
|---|---|
| `apps` | Registry of PSC applications (the extensibility point) |
| `releases` | Versioned releases per app + platform, draft or published |
| `admin_users` | Dashboard authentication |
| `devices` | Registered FCM tokens per app/platform (optional analytics / direct targeting) |
| `notification_logs` | Audit log of sent release notifications, one row per release max |

## Request flow: update check

1. Flutter app calls `POST /api/v1/updates/check` with `app_key`,
   `platform`, `version`, `build_number`.
2. Backend looks up the app by `app_key`; 404s if unknown, returns
   "no update" if inactive.
3. Backend fetches all **published** releases for that
   app + platform, picks the one with the highest semantic version.
4. Compares the client's version against that release's version
   (→ `update_available`) and against its
   `minimum_supported_version` (→ `update_required`).
5. Returns only what the client needs to render a dialog — no
   internal IDs, no admin data.

## Security notes

- Public endpoints: `POST /api/v1/updates/check` (rate-limited, input
  validated, only exposes update metadata) and
  `POST /api/v1/notifications/devices/register` (device self-registers
  its own FCM token; can't read or affect other data).
- Everything else under `/api/v1/apps`, `/api/v1/releases`,
  `/api/v1/notifications/send`, `/api/v1/notifications/history`
  requires a valid admin JWT (`Depends(get_current_admin)`).
- A global exception handler prevents stack traces or internal error
  detail from ever reaching a client.
