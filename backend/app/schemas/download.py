from pydantic import BaseModel


class DownloadInfoOut(BaseModel):
    app_key: str
    app_name: str
    platform: str
    version: str
    build_number: int
    file_name: str | None = None
    file_size_bytes: int | None = None
    download_url: str
    release_notes: list[str] = []
