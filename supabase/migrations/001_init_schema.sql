-- PSC Centralized App Update Management System
-- Initial schema migration

create extension if not exists "uuid-ossp";
create extension if not exists pgcrypto;

-- =========================================================
-- apps
-- =========================================================
create table if not exists apps (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    app_key text not null unique,
    package_name text not null,
    platform text not null default 'both' check (platform in ('android', 'ios', 'both')),
    description text,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_apps_app_key on apps (app_key);
create index if not exists idx_apps_is_active on apps (is_active);

-- =========================================================
-- releases
-- =========================================================
create table if not exists releases (
    id uuid primary key default gen_random_uuid(),
    application_id uuid not null references apps (id) on delete cascade,
    platform text not null check (platform in ('android', 'ios')),
    version text not null,
    build_number integer not null,
    release_title text,
    release_notes text[],
    minimum_supported_version text not null,
    is_mandatory boolean not null default false,
    update_url text not null,
    is_published boolean not null default false,
    release_date timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    constraint uq_release_app_platform_version unique (application_id, platform, version)
);

create index if not exists idx_releases_application_id on releases (application_id);
create index if not exists idx_releases_platform on releases (platform);
create index if not exists idx_releases_version on releases (version);
create index if not exists idx_releases_published on releases (is_published);
create index if not exists idx_releases_app_platform_published
    on releases (application_id, platform, is_published);

-- =========================================================
-- admin_users
-- =========================================================
create table if not exists admin_users (
    id uuid primary key default gen_random_uuid(),
    email text not null unique,
    hashed_password text not null,
    full_name text,
    role text not null default 'admin' check (role in ('admin', 'superadmin')),
    is_active boolean not null default true,
    last_login_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_admin_users_email on admin_users (email);

-- =========================================================
-- devices (for FCM targeting / optional analytics)
-- =========================================================
create table if not exists devices (
    id uuid primary key default gen_random_uuid(),
    application_id uuid not null references apps (id) on delete cascade,
    platform text not null check (platform in ('android', 'ios')),
    fcm_token text not null unique,
    app_version text,
    last_seen_at timestamptz default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_devices_application_id on devices (application_id);
create index if not exists idx_devices_fcm_token on devices (fcm_token);

-- =========================================================
-- notification_logs
-- =========================================================
create table if not exists notification_logs (
    id uuid primary key default gen_random_uuid(),
    application_id uuid not null references apps (id) on delete cascade,
    release_id uuid references releases (id) on delete set null,
    title text not null,
    message text not null,
    fcm_topic text not null,
    status text not null default 'pending' check (status in ('pending', 'sent', 'failed')),
    targeted_device_count integer,
    sent_at timestamptz,
    created_at timestamptz not null default now(),

    -- prevent accidental duplicate notifications for the same release
    constraint uq_notification_release unique (release_id)
);

create index if not exists idx_notification_logs_application_id on notification_logs (application_id);
create index if not exists idx_notification_logs_release_id on notification_logs (release_id);

-- =========================================================
-- updated_at triggers
-- =========================================================
create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_apps_updated_at on apps;
create trigger trg_apps_updated_at before update on apps
    for each row execute function set_updated_at();

drop trigger if exists trg_releases_updated_at on releases;
create trigger trg_releases_updated_at before update on releases
    for each row execute function set_updated_at();

drop trigger if exists trg_admin_users_updated_at on admin_users;
create trigger trg_admin_users_updated_at before update on admin_users
    for each row execute function set_updated_at();

drop trigger if exists trg_devices_updated_at on devices;
create trigger trg_devices_updated_at before update on devices
    for each row execute function set_updated_at();

-- =========================================================
-- seed data: the 4 current PSC apps
-- =========================================================
insert into apps (name, app_key, package_name, platform, description, is_active)
values
    ('PSC Notes',     'psc_notes',     'com.psc.notes',     'both', 'PSC Notes application', true),
    ('PSC Calendar',  'psc_calendar',  'com.psc.calendar',  'both', 'PSC Calendar application', true),
    ('PSC Savings',   'psc_savings',   'com.psc.savings',   'both', 'PSC Savings application', true),
    ('PSC Inventory', 'psc_inventory', 'com.psc.inventory', 'both', 'PSC Inventory application', true)
on conflict (app_key) do nothing;

-- Row Level Security: lock tables down. All access goes through the
-- FastAPI backend using the service-role key, never the anon key.
alter table apps enable row level security;
alter table releases enable row level security;
alter table admin_users enable row level security;
alter table devices enable row level security;
alter table notification_logs enable row level security;

-- No policies are created for anon/authenticated roles on purpose:
-- the backend uses the service_role key (which bypasses RLS) so that
-- privileged Supabase credentials never need to be exposed to clients.
