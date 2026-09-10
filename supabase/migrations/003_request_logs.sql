-- Request / client activity logs for the admin Logs page.
-- Captures update-check and device-register events with client IP.

create table if not exists request_logs (
    id uuid primary key default gen_random_uuid(),
    event_type text not null check (event_type in ('update_check', 'device_register')),
    application_id uuid references apps (id) on delete set null,
    app_key text,
    platform text check (platform is null or platform in ('android', 'ios')),
    app_version text,
    build_number integer,
    ip_address text,
    user_agent text,
    -- Free-form outcome metadata, e.g. update_available / registered
    result text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create index if not exists idx_request_logs_created_at on request_logs (created_at desc);
create index if not exists idx_request_logs_app_key on request_logs (app_key);
create index if not exists idx_request_logs_event_type on request_logs (event_type);
create index if not exists idx_request_logs_ip_address on request_logs (ip_address);
create index if not exists idx_request_logs_application_id on request_logs (application_id);

alter table request_logs enable row level security;
