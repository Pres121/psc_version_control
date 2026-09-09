from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.releases import _validate_release_sequence
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


@pytest.mark.parametrize(
    ("version", "build_number", "message"),
    [
        ("1.1.0", 11, "already exists"),
        ("1.0.9", 12, "Version must be higher"),
        ("1.2.0", 10, "Build number must be higher"),
    ],
)
def test_release_sequence_rejects_duplicate_or_non_increasing_values(
    version: str, build_number: int, message: str
):
    existing = [
        {"version": "1.0.0", "build_number": 10},
        {"version": "1.1.0", "build_number": 11},
    ]

    with pytest.raises(HTTPException, match=message):
        _validate_release_sequence(version, build_number, existing)


def test_release_sequence_accepts_higher_version_and_build():
    _validate_release_sequence(
        "1.2.0",
        12,
        [{"version": "1.1.0", "build_number": 11}],
    )
