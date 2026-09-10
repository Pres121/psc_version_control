-- In-app announcements (no FCM / Firebase required).
-- PSC apps poll these on launch and show an in-app dialog.

create table if not exists in_app_announcements (
    id uuid primary key default gen_random_uuid(),
    application_id uuid not null references apps (id) on delete cascade,
    release_id uuid references releases (id) on delete set null,
    title text not null,
    message text not null,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_in_app_announcements_app_active
    on in_app_announcements (application_id, is_active, created_at desc);

drop trigger if exists trg_in_app_announcements_updated_at on in_app_announcements;
create trigger trg_in_app_announcements_updated_at before update on in_app_announcements
    for each row execute function set_updated_at();

alter table in_app_announcements enable row level security;
