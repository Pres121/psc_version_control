-- In-app announcements (no FCM / Firebase required).
-- One-shot messages: publish once; each device shows each announcement at most once.
-- Not tied to releases. No activate/deactivate — create a new row to send again.

create table if not exists in_app_announcements (
    id uuid primary key default gen_random_uuid(),
    application_id uuid not null references apps (id) on delete cascade,
    title text not null,
    message text not null,
    created_at timestamptz not null default now()
);

create index if not exists idx_in_app_announcements_app_created
    on in_app_announcements (application_id, created_at desc);

alter table in_app_announcements enable row level security;
