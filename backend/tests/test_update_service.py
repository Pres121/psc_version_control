from unittest.mock import MagicMock, patch

from app.schemas.update import UpdateCheckRequest
from app.services.update_service import check_for_update


def _mock_table(app_row, releases_rows):
    """Build a fake supabase client whose .table(name)... chain returns
    canned data depending on which table is queried."""
    mock_client = MagicMock()

    def table_side_effect(name):
        query = MagicMock()
        if name == "apps":
            query.select.return_value = query
            query.eq.return_value = query
            query.limit.return_value = query
            query.execute.return_value = MagicMock(data=[app_row] if app_row else [])
        elif name == "releases":
            query.select.return_value = query
            query.eq.return_value = query
            query.execute.return_value = MagicMock(data=releases_rows)
        return query

    mock_client.table.side_effect = table_side_effect
    return mock_client


@patch("app.services.update_service.get_supabase")
def test_update_available_optional(mock_get_supabase):
    app_row = {"id": "app-1", "name": "PSC Notes", "is_active": True}
    releases = [
        {
            "version": "1.4.0",
            "build_number": 14,
            "release_title": "New version available",
            "release_notes": ["Added categories"],
            "minimum_supported_version": "1.2.0",
            "is_mandatory": False,
            "update_url": "https://play.google.com/store/apps/details?id=com.psc.notes",
        }
    ]
    mock_get_supabase.return_value = _mock_table(app_row, releases)

    req = UpdateCheckRequest(app_key="psc_notes", platform="android", version="1.3.0", build_number=13)
    result = check_for_update(req)

    assert result.update_available is True
    assert result.update_required is False
    assert result.latest_version == "1.4.0"


@patch("app.services.update_service.get_supabase")
def test_update_required_mandatory(mock_get_supabase):
    app_row = {"id": "app-1", "name": "PSC Notes", "is_active": True}
    releases = [
        {
            "version": "2.0.0",
            "build_number": 20,
            "release_title": "Critical update",
            "release_notes": [],
            "minimum_supported_version": "1.7.0",
            "is_mandatory": True,
            "update_url": "https://play.google.com/store/apps/details?id=com.psc.notes",
        }
    ]
    mock_get_supabase.return_value = _mock_table(app_row, releases)

    req = UpdateCheckRequest(app_key="psc_notes", platform="android", version="1.5.0", build_number=5)
    result = check_for_update(req)

    assert result.update_available is True
    assert result.update_required is True


@patch("app.services.update_service.get_supabase")
def test_up_to_date_but_below_minimum_is_not_required(mock_get_supabase):
    app_row = {"id": "app-1", "name": "PSC Notes", "is_active": True}
    releases = [
        {
            "version": "2.0.0",
            "build_number": 20,
            "release_title": "Critical update",
            "release_notes": [],
            "minimum_supported_version": "1.7.0",
            "is_mandatory": True,
            "update_url": "https://play.google.com/store/apps/details?id=com.psc.notes",
        }
    ]
    mock_get_supabase.return_value = _mock_table(app_row, releases)

    req = UpdateCheckRequest(app_key="psc_notes", platform="android", version="1.8.0", build_number=8)
    result = check_for_update(req)

    assert result.update_available is True
    assert result.update_required is False


@patch("app.services.update_service.get_supabase")
def test_no_releases_returns_no_update(mock_get_supabase):
    app_row = {"id": "app-1", "name": "PSC Notes", "is_active": True}
    mock_get_supabase.return_value = _mock_table(app_row, [])

    req = UpdateCheckRequest(app_key="psc_notes", platform="android", version="1.0.0", build_number=1)
    result = check_for_update(req)

    assert result.update_available is False
    assert result.update_required is False
