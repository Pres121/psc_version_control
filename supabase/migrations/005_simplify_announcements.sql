-- Simplify announcements to one-shot publishes (no release link, no activate toggle).
-- Safe to run if 004 already created the older columns.

alter table in_app_announcements drop column if exists release_id;
alter table in_app_announcements drop column if exists is_active;
alter table in_app_announcements drop column if exists updated_at;

drop index if exists idx_in_app_announcements_app_active;
create index if not exists idx_in_app_announcements_app_created
    on in_app_announcements (application_id, created_at desc);

drop trigger if exists trg_in_app_announcements_updated_at on in_app_announcements;
