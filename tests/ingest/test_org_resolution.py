import pytest
from unittest.mock import Mock, patch

from core.ingest.org_resolution import (
    resolve_from_payload,
    apply_intramural_rule,
    is_org_complete,
    resolve_from_prior_db,
    resolve_from_cache,
    resolve_from_future_api,
    resolve_org,
)

# ----------------------------------------
# TESTS FOR resolve_from_payload
# ----------------------------------------


def test_resolve_from_payload_complete():
    """Test that resolve_from_payload returns the correct organization information when all fields are present."""

    organization = {
        "org_name": "Harvard Medical School",
        "org_city": "Boston",
        "org_state": "MA",
        "org_country": "United States",
    }

    org = resolve_from_payload(organization)

    assert org == {
        "name": "Harvard Medical School",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }


def test_resolve_from_payload_normalizes_fields():
    """Test that resolve_from_payload normalizes organization fields by stripping whitespace and capitalizing words."""

    organization = {
        "org_name": "  harvard medical school ",
        "org_city": " boston ",
        "org_state": " ma ",
        "org_country": " united states ",
    }

    org = resolve_from_payload(organization)

    assert org == {
        "name": "Harvard Medical School",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }


def test_resolve_from_payload_missing_fields():

    organization = {
        "org_name": "",
        "org_city": None,
        "org_state": "",
        "org_country": None,
    }

    org = resolve_from_payload(organization)

    assert org == {
        "name": None,
        "city": None,
        "state": None,
        "country": None,
    }


@pytest.mark.parametrize(
    "organization",
    [
        None,
        {},
    ],
)
def test_resolve_from_payload_none(organization):
    """Test that resolve_from_payload returns None for None or empty organization payloads."""

    assert resolve_from_payload(organization) is None


# ----------------------------------------
# TESTS FOR apply_intramural_rule
# ----------------------------------------


def test_apply_intramural_rule_non_intramural():
    """Test that apply_intramural_rule returns the original organization for non-intramural grants."""

    org = {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }

    resolved = apply_intramural_rule(
        "R01CA123456",
        org,
        "NIH",
    )

    assert resolved == org


def test_apply_intramural_rule_nih_defaults():

    resolved = apply_intramural_rule(
        "ZIAHG000001",
        None,
        "NIH",
    )

    assert resolved == {
        "name": "NIH Intramural Program",
        "city": "Bethesda",
        "state": "MD",
        "country": "United States",
    }


def test_apply_intramural_rule_fda_defaults():
    """Test that apply_intramural_rule returns the correct default organization for FDA intramural grants."""

    resolved = apply_intramural_rule(
        "Z01FD000001",
        None,
        "FDA",
    )

    assert resolved == {
        "name": "FDA Intramural Program",
        "city": "Bethesda",
        "state": "MD",
        "country": "United States",
    }


def test_apply_intramural_rule_preserves_existing_values():
    """Test that apply_intramural_rule preserves existing organization values for intramural grants."""

    org = {
        "name": "National Cancer Institute",
        "city": "Frederick",
        "state": "MD",
        "country": "United States",
    }

    resolved = apply_intramural_rule(
        "ZIAHG000001",
        org,
        "NIH",
    )

    assert resolved == org


# ----------------------------------------
# TESTS FOR is_org_complete
# ----------------------------------------


def test_is_org_complete_us():

    org = {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }

    assert is_org_complete(org) is True


@pytest.mark.parametrize(
    "missing_field",
    [
        "name",
        "city",
        "country",
    ],
)
def test_is_org_complete_missing_required_field(missing_field):
    """Test that is_org_complete returns False if any required field is missing."""

    org = {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }

    org[missing_field] = None

    assert is_org_complete(org) is False


def test_is_org_complete_missing_state_us():
    """Test that is_org_complete returns False if state is missing for a US organization."""

    org = {
        "name": "Harvard",
        "city": "Boston",
        "state": None,
        "country": "United States",
    }

    assert is_org_complete(org) is False


def test_is_org_complete_non_us_no_state_required():
    """Test that is_org_complete returns True if state is missing for a non-US organization."""

    org = {
        "name": "University of Toronto",
        "city": "Toronto",
        "state": None,
        "country": "Canada",
    }

    assert is_org_complete(org) is True


@pytest.mark.parametrize(
    "org",
    [
        None,
        {},
    ],
)
def test_is_org_complete_none(org):
    """Test that is_org_complete returns False for None or empty organization."""

    assert is_org_complete(org) is False


# ----------------------------------------
# TESTS FOR resolve_from_prior_db
# ----------------------------------------


def test_resolve_from_prior_db_current_year():

    cur = Mock()

    cur.fetchone.side_effect = [
        (
            "Harvard",
            "Boston",
            "MA",
            "United States",
        )
    ]

    org = resolve_from_prior_db(
        cur,
        "R01CA123456",
        2025,
    )

    cur.execute.assert_called_once_with(
        """
            SELECT o.name, o.city, o.state, o.country
            FROM ResearchGrants rg
            JOIN Organizations o ON rg.organization_id = o.id
            WHERE rg.core_project_num = %s AND rg.fiscal_year = %s
            AND o.name IS NOT NULL AND o.city IS NOT NULL AND o.country IS NOT NULL
            LIMIT 1
        """,
        ("R01CA123456", 2025),
    )

    assert org == {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }


def test_resolve_from_prior_db_previous_year():
    """Test that resolve_from_prior_db returns organization information from the previous fiscal year if not found for the current year."""

    cur = Mock()

    cur.fetchone.side_effect = [
        None,
        (
            "Harvard",
            "Boston",
            "MA",
            "United States",
        ),
    ]

    org = resolve_from_prior_db(
        cur,
        "R01CA123456",
        2025,
    )

    assert cur.execute.call_count == 2

    assert org == {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }


def test_resolve_from_prior_db_not_found():
    """Test that resolve_from_prior_db returns None if no organization is found for the given core project number and fiscal year."""

    cur = Mock()

    cur.fetchone.side_effect = [
        None,
        None,
    ]

    org = resolve_from_prior_db(
        cur,
        "R01CA123456",
        2025,
    )

    assert cur.execute.call_count == 2

    assert org is None


# ----------------------------------------
# TESTS FOR resolve_from_cache
# ----------------------------------------


def test_resolve_from_cache_hit():
    """Test that resolve_from_cache returns the organization information from the cache if it exists."""

    cache = {
        "R01CA123456": {
            "name": "Harvard",
            "city": "Boston",
            "state": "MA",
            "country": "United States",
        }
    }

    org = resolve_from_cache(
        "R01CA123456",
        cache,
    )

    assert org == {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }


def test_resolve_from_cache_miss():
    """Test that resolve_from_cache returns None if the organization information is not in the cache."""

    cache = {}

    org = resolve_from_cache(
        "R01CA123456",
        cache,
    )

    assert org is None


# ----------------------------------------
# TESTS FOR resolve_from_future_api
# ----------------------------------------


@patch("core.ingest.org_resolution.requests.post")
def test_resolve_from_future_api_success(mock_post):
    """Test that resolve_from_future_api returns the organization information from the API response."""

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "results": [
            {
                "organization": {
                    "org_name": "harvard medical school",
                    "org_city": "boston",
                    "org_state": "ma",
                    "org_country": "united states",
                }
            }
        ]
    }

    mock_post.return_value = response

    org = resolve_from_future_api(
        "R01CA123456",
        2025,
    )

    assert org == {
        "name": "Harvard Medical School",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }

    assert mock_post.call_count == 1


@patch("core.ingest.org_resolution.requests.post")
def test_resolve_from_future_api_exception(mock_post):
    """Test that resolve_from_future_api returns None if the API call raises an exception."""

    mock_post.side_effect = Exception("Connection error")

    org = resolve_from_future_api(
        "R01CA123456",
        2025,
    )

    assert mock_post.call_count == 2
    assert org is None


@patch("core.ingest.org_resolution.requests.post")
def test_resolve_from_future_api_no_results(mock_post):
    """Test that resolve_from_future_api returns None if the API call returns no results."""

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"results": []}

    mock_post.return_value = response

    org = resolve_from_future_api(
        "R01CA123456",
        2025,
    )

    assert mock_post.call_count == 2
    assert org is None


# ----------------------------------------
# TESTS FOR resolve_org
# ----------------------------------------


@patch("core.ingest.org_resolution.is_org_complete")
@patch("core.ingest.org_resolution.apply_intramural_rule")
@patch("core.ingest.org_resolution.resolve_from_payload")
def test_resolve_org_payload(
    mock_payload,
    mock_intramural,
    mock_complete,
):
    """Test that resolve_org returns the organization information from the payload if it is complete."""

    org = {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }

    mock_payload.return_value = org
    mock_intramural.return_value = org
    mock_complete.return_value = True

    result, status = resolve_org(
        cur=Mock(),
        core_project_num="R01CA123456",
        fiscal_year=2025,
        organization={},
        agency_abbr="CA",
        cache={},
        policy={"allow_future_lookup": False, "allow_manual_lookup": False},
    )

    assert result == org
    assert status == "payload"


@patch("core.ingest.org_resolution.resolve_from_prior_db")
@patch("core.ingest.org_resolution.is_org_complete")
@patch("core.ingest.org_resolution.apply_intramural_rule")
@patch("core.ingest.org_resolution.resolve_from_payload")
def test_resolve_org_prior_db(
    mock_payload,
    mock_intramural,
    mock_complete,
    mock_prior_db,
):
    """Test that resolve_org returns the organization information from the prior database if it is complete."""

    org = {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }

    mock_payload.return_value = {}
    mock_intramural.return_value = {}
    mock_complete.return_value = False
    mock_prior_db.return_value = org

    result, status = resolve_org(
        cur=Mock(),
        core_project_num="R01CA123456",
        fiscal_year=2025,
        organization={},
        agency_abbr="CA",
        cache={},
        policy={
            "allow_future_lookup": False,
            "allow_manual_lookup": False,
        },
    )

    assert result == org
    assert status == "prior_db"


@patch("core.ingest.org_resolution.resolve_from_cache")
@patch("core.ingest.org_resolution.resolve_from_prior_db")
@patch("core.ingest.org_resolution.resolve_from_payload")
def test_resolve_org_cache(
    mock_payload,
    mock_prior_db,
    mock_cache,
):
    """Test that resolve_org returns the organization information from the cache if it is complete."""

    org = {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }

    mock_payload.return_value = None
    mock_prior_db.return_value = None
    mock_cache.return_value = org

    result, status = resolve_org(
        cur=Mock(),
        core_project_num="R01CA123456",
        fiscal_year=2025,
        organization={},
        agency_abbr="CA",
        cache={},
        policy={
            "allow_future_lookup": False,
            "allow_manual_lookup": False,
        },
    )

    assert result == org
    assert status == "cache"


@patch("core.ingest.org_resolution.resolve_from_future_api")
@patch("core.ingest.org_resolution.resolve_from_cache")
@patch("core.ingest.org_resolution.resolve_from_prior_db")
@patch("core.ingest.org_resolution.resolve_from_payload")
def test_resolve_org_future_api(
    mock_payload,
    mock_prior_db,
    mock_cache,
    mock_future_api,
):
    """Test that resolve_org returns the organization information from the future API if it is complete."""

    org = {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }

    mock_payload.return_value = None
    mock_prior_db.return_value = None
    mock_cache.return_value = None
    mock_future_api.return_value = org

    result, status = resolve_org(
        cur=Mock(),
        core_project_num="R01CA123456",
        fiscal_year=2025,
        organization={},
        agency_abbr="CA",
        cache={},
        policy={
            "allow_future_lookup": True,
            "allow_manual_lookup": False,
        },
    )

    assert result == org
    assert status == "future_api"


@patch("core.ingest.org_resolution.resolve_from_future_api")
@patch("core.ingest.org_resolution.resolve_from_cache")
@patch("core.ingest.org_resolution.resolve_from_prior_db")
@patch("core.ingest.org_resolution.resolve_from_payload")
def test_resolve_org_missing(
    mock_payload,
    mock_prior_db,
    mock_cache,
    mock_future_api,
):
    """Test that resolve_org returns None if no organization information is found from any source."""

    mock_payload.return_value = None
    mock_prior_db.return_value = None
    mock_cache.return_value = None
    mock_future_api.return_value = None

    result, status = resolve_org(
        cur=Mock(),
        core_project_num="R01CA123456",
        fiscal_year=2025,
        organization={},
        agency_abbr="CA",
        cache={},
        policy={
            "allow_future_lookup": True,
            "allow_manual_lookup": False,
        },
    )

    assert result is None
    assert status == "missing"


@patch("builtins.input")
@patch("core.ingest.org_resolution.resolve_from_future_api")
@patch("core.ingest.org_resolution.resolve_from_cache")
@patch("core.ingest.org_resolution.resolve_from_prior_db")
@patch("core.ingest.org_resolution.resolve_from_payload")
def test_resolve_org_manual(
    mock_payload,
    mock_prior_db,
    mock_cache,
    mock_future_api,
    mock_input,
):
    """Test that resolve_org prompts the user for manual input if no organization information is found from any source and manual lookup is allowed."""

    mock_payload.return_value = None
    mock_prior_db.return_value = None
    mock_cache.return_value = None
    mock_future_api.return_value = None

    mock_input.side_effect = [
        "Harvard",
        "Boston",
        "United States",
        "MA",
    ]

    result, status = resolve_org(
        cur=Mock(),
        core_project_num="R01CA123456",
        fiscal_year=2025,
        organization={},
        agency_abbr="CA",
        cache={},
        policy={
            "allow_future_lookup": False,
            "allow_manual_lookup": True,
        },
    )

    assert result == {
        "name": "Harvard",
        "city": "Boston",
        "state": "MA",
        "country": "United States",
    }

    assert status == "manual"
