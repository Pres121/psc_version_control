# API Reference

Base URL: `{API_BASE}/api/v1` (e.g. `https://psc-version-control.onrender.com/api/v1`)

Full interactive docs are also available at `/docs` (Swagger) and
`/redoc` when `DOCS_ENABLED=true`.

## Public endpoints (no auth required)

### `POST /updates/check`

Used by every PSC Flutter app on launch. Rate-limited (default
60/minute per IP).

**Request**
```json
{
  "app_key": "psc_notes",
  "platform": "android",
  "version": "1.3.0",
  "build_number": 13
}
```

**Response — update available (optional)**
```json
{
  "update_available": true,
  "update_required": false,
  "latest_version": "1.4.0",
  "latest_build": 14,
  "minimum_supported_version": "1.2.0",
  "title": "New version available",
  "message": "PSC Notes has been updated with new features and improvements.",
  "release_notes": ["Added note categories", "Improved search", "Bug fixes"],
  "update_url": "https://play.google.com/store/apps/details?id=com.psc.notes"
}
```

**Response — no update**
```json
{ "update_available": false, "update_required": false }
```

`update_required: true` means the installed version is below the
release's `minimum_supported_version` — the client should show the
non-dismissible update dialog.

### `POST /notifications/devices/register`

Called by the Flutter update service (or your own FCM setup code) to
associate a device's FCM token with an app, so it can be included in
future topic-based notifications.

```json
{ "app_key": "psc_notes", "platform": "android", "fcm_token": "...", "app_version": "1.3.0" }
```

## Admin endpoints (require `Authorization: Bearer <JWT>`)

### `POST /auth/login`
```json
{ "email": "admin@psc.com", "password": "..." }
```
→ `{ "access_token": "...", "token_type": "bearer" }`

### `GET /auth/me`
Returns the current admin's profile.

### Applications
- `GET /apps` — list all
- `POST /apps` — create `{ name, app_key, package_name, platform, description, is_active }`
- `GET /apps/{id}` — detail
- `PATCH /apps/{id}` — partial update (e.g. `{ "is_active": false }`)
- `GET /apps/{id}/releases` — release history for one app

### Releases
- `GET /releases?application_id=&platform=` — list, filterable
- `POST /releases` — create a draft release (`is_published: false`)
- `GET /releases/{id}` — detail
- `PATCH /releases/{id}` — partial update
- `POST /releases/{id}/publish` — publish a release (dashboard shows a
  confirmation dialog before calling this)

### Notifications
- `POST /notifications/send` — `{ application_id, release_id, title, message }`.
  Fails with 409 if a notification was already sent for that
  `release_id` (duplicate protection).
- `GET /notifications/history?application_id=` — notification log

## Error format

All errors return:
```json
{ "detail": "human-readable message" }
```
Unhandled server errors always return a generic `500` with
`{"detail": "Internal server error"}` — no stack traces or internal
details are ever exposed.
