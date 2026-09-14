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
associate a device's FCM token with an app. The backend upserts the
token, refreshes `last_seen_at`, and **subscribes the token to the
app's `app_key` FCM topic** when FCM credentials are configured.

```json
{ "app_key": "psc_notes", "platform": "android", "fcm_token": "...", "app_version": "1.3.0" }
```

→ `{ "registered": true, "topic": "psc_notes" }`

### Admin activity logs

### `GET /logs?event_type=&app_key=&ip_address=&limit=100`

Requires admin JWT. Returns recent client activity (newest first), including
the requester IP for update checks and device registrations.

Example row fields: `event_type`, `app_key`, `platform`, `app_version`,
`build_number`, `ip_address`, `user_agent`, `result`, `metadata`, `created_at`.

`event_type` is one of `update_check` | `device_register`.

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
- `PATCH /releases/{id}` — edit a release. Requires the editable fields plus
  `{ "app_key": "psc_notes" }` to confirm.
- `POST /releases/{id}/publish` — publish a release. Body: `{ "app_key": "psc_notes" }`.
- `POST /releases/{id}/unpublish` — remove a release from update checks.
  Same confirmation body.
- `DELETE /releases/{id}` — permanently delete a release. Same confirmation body.

Confirmation only requires re-entering the app key. Release creation and
version/build edits reject duplicate versions, lower versions, and build
numbers that do not increase for that app/platform.

### Notifications
- `POST /notifications/send` — `{ application_id, release_id, title, message }`.
  Fails with 409 if a notification was already sent for that
  `release_id` (duplicate protection). Records `targeted_device_count`
  from registered devices for that app.
- `GET /notifications/history?application_id=` — notification log

### Downloads (public)
- `GET /download/{app_key}?platform=android` — branded HTML page; auto-starts download
- `GET /downloads/{app_key}?platform=android` — JSON with signed download URL + metadata

### Releases (admin)
- `POST /releases/{id}/upload` — multipart form field `file` (`.apk` / `.ipa` / `.zip`).
  Overwrites the latest binary for that app+platform and sets `update_url` to the
  PSC download page.

## Error format

All errors return:
```json
{ "detail": "human-readable message" }
```
Unhandled server errors always return a generic `500` with
`{"detail": "Internal server error"}` — no stack traces or internal
details are ever exposed.
