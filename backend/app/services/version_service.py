"""
Reliable semantic version comparison.

Handles versions like 1.0.0, 1.10.0, 2.0.0, 1.2.5-beta.1, etc.
Never compare versions as plain strings ("1.10.0" < "1.9.0" lexically,
which is wrong) - always parse into numeric components first.
"""
import re
from functools import cmp_to_key

_SEMVER_RE = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<pre>[0-9A-Za-z\-.]+))?$"
)


def is_valid_semver(version: str) -> bool:
    return bool(_SEMVER_RE.match(version.strip()))


def parse_version(version: str) -> tuple[int, int, int, str | None]:
    """Parse '1.10.2-beta.1' -> (1, 10, 2, 'beta.1'). Raises ValueError if invalid."""
    match = _SEMVER_RE.match(version.strip())
    if not match:
        raise ValueError(f"Invalid semantic version: '{version}'")
    major, minor, patch = (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )
    return major, minor, patch, match.group("pre")


def compare_versions(v1: str, v2: str) -> int:
    """
    Returns:
        -1 if v1 < v2
         0 if v1 == v2
         1 if v1 > v2
    A pre-release version (e.g. 1.0.0-beta) is considered lower than
    its final release (1.0.0), per semver precedence rules.
    """
    major1, minor1, patch1, pre1 = parse_version(v1)
    major2, minor2, patch2, pre2 = parse_version(v2)

    for a, b in ((major1, major2), (minor1, minor2), (patch1, patch2)):
        if a != b:
            return -1 if a < b else 1

    if pre1 == pre2:
        return 0
    if pre1 is None:
        return 1  # v1 is a full release, v2 is a pre-release -> v1 is greater
    if pre2 is None:
        return -1
    # both are pre-release strings: compare lexically as a reasonable fallback
    return -1 if pre1 < pre2 else (1 if pre1 > pre2 else 0)


def is_greater(v1: str, v2: str) -> bool:
    return compare_versions(v1, v2) > 0


def is_less(v1: str, v2: str) -> bool:
    return compare_versions(v1, v2) < 0


def sort_versions(versions: list[str], descending: bool = True) -> list[str]:
    key = cmp_to_key(compare_versions)
    return sorted(versions, key=key, reverse=descending)
