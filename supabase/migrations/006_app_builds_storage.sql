-- App binary storage metadata on releases + Supabase Storage bucket.

alter table releases
    add column if not exists storage_path text,
    add column if not exists file_name text,
    add column if not exists file_size_bytes bigint;

comment on column releases.storage_path is 'Path inside the app-builds storage bucket';
comment on column releases.file_name is 'Original uploaded file name shown on the download page';
comment on column releases.file_size_bytes is 'Uploaded binary size in bytes';

-- Private bucket for APK/IPA builds (service_role uploads; signed URLs for download).
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
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;
