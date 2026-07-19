from core.ingest.reporter_client import API_URL
import requests


def resolve_from_payload(organization: dict):
    """
    Resolves organization information directly from the payload.

    Parameters
    ----------
    organization (dict): A dictionary containing organization data, including 'org_name', 'org_city', 'org_state', and 'org_country'.

    Returns
    -------
    dict or None: A dictionary containing the resolved organization information with keys 'name', 'city', 'state', and 'country'.
    Returns None if the organization data is not provided.
    """

    if not organization:
        return None

    org_name = (organization.get("org_name") or "").title().strip()
    org_city = (organization.get("org_city") or "").title().strip()
    org_state = (organization.get("org_state") or "").upper().strip()
    org_country = (organization.get("org_country") or "").title().strip()

    return {
        "name": org_name or None,
        "city": org_city or None,
        "state": org_state or None,
        "country": org_country or None,
    }


def apply_intramural_rule(core_project_num: str, org: dict, agency_abbr: str):
    """
    Applies the intramural rule for NIH grants. If the core project number starts with "Z",
    it indicates an intramural project, and the organization information is set to a default value
    based on the agency abbreviation.

    Parameters
    ----------
    core_project_num (str): The core project number of the NIH grant.
    org (dict): A dictionary containing organization data, including 'name', 'city', 'state', and 'country'.
    agency_abbr (str): The abbreviation of the agency administering the grant (e.g., "FDA" for the Food and Drug Administration).

    Returns
    -------
    dict: A dictionary containing the resolved organization information with keys 'name', 'city', 'state', and 'country'.
    """

    if not core_project_num.startswith("Z"):
        return org

    if org is None:
        org = {"name": None, "city": None, "state": None, "country": None}

    name = org.get("name")
    city = org.get("city")
    state = org.get("state")
    country = org.get("country")

    if agency_abbr == "FDA":
        name = name or "FDA Intramural Program"
    else:
        name = name or "NIH Intramural Program"

    city = city or "Bethesda"
    state = state or "MD"
    country = country or "United States"

    return {"name": name, "city": city, "state": state, "country": country}


def is_org_complete(org: dict) -> bool:
    """
    Checks if the organization information is complete.

    Parameters
    ----------
    org (dict): A dictionary containing organization data, including 'name', 'city', 'state', and 'country'.

    Returns
    -------
    bool: True if the organization information is complete, False otherwise.
    """

    if not org:
        return False

    required = ["name", "city", "country"]
    for field in required:
        if not org.get(field):
            return False

    # State only required for US orgs
    if org.get("country") == "United States" and not org.get("state"):
        return False

    return True


def resolve_from_prior_db(cur, core_project_num: str, fiscal_year: int) -> dict:
    """
    Attempts to resolve organization information from prior database records for the same core project number.

    Parameters
    ----------
    cur: A database cursor for executing SQL queries.
    core_project_num (str): The core project number of the NIH grant.
    fiscal_year (int): The fiscal year of the NIH grant.
    organization (dict): A dictionary containing organization data, including 'name', 'city', 'state', and 'country'.

    Returns
    -------
    dict or None: A dictionary containing the resolved organization information with keys 'name', 'city', 'state', and 'country'.
    Returns None if no prior record is found or if the organization
    information is incomplete.
    """

    for org_year in [fiscal_year, fiscal_year - 1]:
        cur.execute(
            """
            SELECT o.name, o.city, o.state, o.country
            FROM ResearchGrants rg
            JOIN Organizations o ON rg.organization_id = o.id
            WHERE rg.core_project_num = %s AND rg.fiscal_year = %s
            AND o.name IS NOT NULL AND o.city IS NOT NULL AND o.country IS NOT NULL
            LIMIT 1
        """,
            (core_project_num, org_year),
        )
        previous_org = cur.fetchone()
        if previous_org:
            org_name, org_city, org_state, org_country = previous_org
            return {
                "name": org_name,
                "city": org_city,
                "state": org_state,
                "country": org_country,
            }


def resolve_from_cache(core_project_num: str, cache: dict):
    """
    Attempts to resolve organization information from a cache.

    Parameters
    ----------
    core_project_num (str): The core project number of the NIH grant.
    cache (dict): A dictionary containing cached organization information, where the keys are core project numbers
    and the values are dictionaries with keys 'name', 'city', 'state', and 'country'.

    Returns
    -------
    dict or None: A dictionary containing the resolved organization information with keys 'name', 'city', 'state', and 'country'.
    Returns None if no cached record is found.
    """

    org = cache.get(core_project_num)
    return org.copy() if org else None


def resolve_from_future_api(core_project_num: str, current_fy: int):
    """
    Attempts to retrieve missing org info by querying next 2 fiscal years.

    Parameters
    ----------
    core_project_num (str): The core project number of the NIH grant.
    current_fy (int): The current fiscal year.

    Returns
    -------
    dict or None: A dictionary containing the resolved organization information with keys 'name', 'city', 'state', and 'country'.
    Returns None if no future record is found.
    """

    for year in [current_fy + 1, current_fy + 2]:
        payload = {
            "criteria": {
                "fiscal_years": [year],
                "core_project_nums": [core_project_num],
            },
            "offset": 0,
            "limit": 1,
        }
        try:
            response = requests.post(API_URL, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception:
            continue
        results = data.get("results", [])
        if not results:
            continue

        org = results[0].get("organization", {})
        name = (org.get("org_name") or "").title().strip()
        city = (org.get("org_city") or "").title().strip()
        state = (org.get("org_state") or "").upper().strip()
        country = (org.get("org_country") or "").title().strip()

        if name and city and country:
            return {"name": name, "city": city, "state": state, "country": country}
    return None


def resolve_org(
    *,
    cur,
    core_project_num: str,
    fiscal_year: int,
    organization: dict,
    agency_abbr: str,
    cache: dict,
    policy: dict,
):
    """
    Resolves organization information for a given NIH grant result using multiple strategies,
    including payload data, prior database records, cache, and future API lookups.

    Parameters
    ----------
    cur: A database cursor for executing SQL queries.
    core_project_num (str): The core project number of the NIH grant.
    fiscal_year (int): The fiscal year of the NIH grant.
    organization (dict): A dictionary containing organization data, including 'name', 'city', 'state', and 'country'.
    agency_abbr (str): The abbreviation of the agency administering the grant (e.g., "FDA" for the Food and Drug Administration).
    cache (dict): A dictionary containing cached organization information, where the keys are core project numbers
    and the values are dictionaries with keys 'name', 'city', 'state', and 'country'.
    policy (dict): A dictionary containing policy settings for organization resolution, including 'allow_future_lookup' and 'allow_manual_lookup'.

    Returns
    -------
    tuple: A tuple containing the resolved organization information (dict) and the resolution status (str).
    The resolution status can be one of the following:
        - "payload": Resolved from payload data.
        - "prior_db": Resolved from prior database records.
        - "cache": Resolved from cache.
        - "future_api": Resolved from future API lookups.
        - "manual": Resolved through manual input (if allowed).
        - "missing": Could not resolve organization information.
    """

    # First, try to resolve from payload
    org = resolve_from_payload(organization)
    if org:
        # apply intramural rule if applicable
        org = apply_intramural_rule(core_project_num, org, agency_abbr)
        if is_org_complete(org):
            return org, "payload"

    # Next, try to resolve from prior database records
    org = resolve_from_prior_db(cur, core_project_num, fiscal_year, organization)
    if org:
        return org, "prior_db"

    # Next, try to resolve from cache
    org = resolve_from_cache(core_project_num, cache)
    if org:
        return org, "cache"

    # Next, try to resolve from future API
    if policy["allow_future_lookup"]:
        org = resolve_from_future_api(core_project_num, fiscal_year)
        if org:
            return org, "future_api"

    # manual lookup could be added here
    if policy["allow_manual_lookup"]:
        if not org:
            org_name = (
                input(f"Enter organization name for core project {core_project_num}: ")
                .title()
                .strip()
            )
            org_city = input("Enter city: ").title().strip()
            org_country = input("Enter country: ").title().strip()
            if org_country == "United States":
                org_state = input("Enter state (2-letter code): ").upper().strip()
            else:
                org_state = ""
            return {
                "name": org_name,
                "city": org_city,
                "state": org_state,
                "country": org_country,
            }, "manual"

    return None, "missing"
