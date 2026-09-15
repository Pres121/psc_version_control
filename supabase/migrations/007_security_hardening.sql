-- Security hardening: ensure RLS on all app tables + lock down storage.objects
-- for the private app-builds bucket (service_role only; signed URLs for clients).

-- Tables that must never be readable via anon/authenticated keys
alter table if exists apps enable row level security;
alter table if exists releases enable row level security;
alter table if exists admin_users enable row level security;
alter table if exists devices enable row level security;
alter table if exists notification_logs enable row level security;
alter table if exists request_logs enable row level security;
alter table if exists in_app_announcements enable row level security;

-- Explicit deny: no policies for anon/authenticated means zero direct client access.
-- (service_role bypasses RLS — FastAPI uses that key only.)

-- Storage: keep bucket private and deny direct object access for anon/authenticated.
update storage.buckets
set public = false
where id = 'app-builds';

-- Drop any accidental open policies on this bucket if they exist
drop policy if exists "Public read app-builds" on storage.objects;
drop policy if exists "Public upload app-builds" on storage.objects;
drop policy if exists "Anon read app-builds" on storage.objects;
drop policy if exists "Authenticated read app-builds" on storage.objects;
drop policy if exists "Authenticated upload app-builds" on storage.objects;

-- No SELECT/INSERT/UPDATE/DELETE policies for anon or authenticated on app-builds.
-- Downloads go through FastAPI → create_signed_url (service_role).
-- Optional: allow service_role policies are unnecessary because service_role bypasses RLS.

-- Ensure bucket exists (idempotent with 006)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
    'app-builds',
    'app-builds',
    false,
    524288000,
    array[
        'application/vnd.android.package-archive',
        'application/octet-stream',
        'application/zip',
        'application/x-zip-compressed',
        'application/iphone'
    ]
)
on conflict (id) do update
set
    public = false,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;
