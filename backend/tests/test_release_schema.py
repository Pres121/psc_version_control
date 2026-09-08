from uuid import uuid4

from app.schemas.release import ReleaseCreate


def test_release_accepts_no_store_url():
    release = ReleaseCreate(
        application_id=uuid4(),
        platform="android",
        version="1.0.0",
        build_number=1,
        minimum_supported_version="1.0.0",
    )

    assert release.update_url is None
