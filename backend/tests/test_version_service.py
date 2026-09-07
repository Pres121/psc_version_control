import pytest

from app.services.version_service import (
    compare_versions,
    is_greater,
    is_less,
    is_valid_semver,
    sort_versions,
)


def test_is_valid_semver():
    assert is_valid_semver("1.0.0")
    assert is_valid_semver("1.10.0")
    assert is_valid_semver("1.2.3-beta.1")
    assert not is_valid_semver("1.0")
    assert not is_valid_semver("v1.0.0")
    assert not is_valid_semver("abc")


def test_numeric_not_lexical_comparison():
    # The classic bug: "1.10.0" < "1.9.0" as strings, but > as versions.
    assert is_greater("1.10.0", "1.9.0")
    assert compare_versions("1.10.0", "1.9.0") == 1


@pytest.mark.parametrize(
    "v1,v2,expected",
    [
        ("1.0.0", "1.0.0", 0),
        ("1.1.0", "1.0.0", 1),
        ("1.0.0", "1.1.0", -1),
        ("2.0.0", "1.9.9", 1),
        ("1.2.5", "1.2.4", 1),
        ("1.0.0-beta", "1.0.0", -1),
        ("1.0.0", "1.0.0-beta", 1),
    ],
)
def test_compare_versions(v1, v2, expected):
    assert compare_versions(v1, v2) == expected


def test_sort_versions():
    versions = ["1.9.0", "1.10.0", "2.0.0", "1.2.5"]
    assert sort_versions(versions, descending=True) == ["2.0.0", "1.10.0", "1.9.0", "1.2.5"]


def test_invalid_version_raises():
    with pytest.raises(ValueError):
        compare_versions("not-a-version", "1.0.0")
