-- OTP challenges for admin login (email codes via Resend).

create table if not exists admin_otps (
    id uuid primary key default gen_random_uuid(),
    admin_user_id uuid not null references admin_users (id) on delete cascade,
    code_hash text not null,
    expires_at timestamptz not null,
    consumed_at timestamptz,
    attempt_count integer not null default 0,
    created_at timestamptz not null default now()
);

create index if not exists idx_admin_otps_admin_user_id on admin_otps (admin_user_id);
create index if not exists idx_admin_otps_expires_at on admin_otps (expires_at);

alter table admin_otps enable row level security;
