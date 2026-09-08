-- Existing installations created with 001 required an update URL. Releases
-- distributed directly or through managed devices do not always have one.
alter table releases
    alter column update_url drop not null;
