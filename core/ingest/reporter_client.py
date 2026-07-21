# this script contains functions to interact with the NIH Reporter API

import requests
import random

API_URL = "https://api.reporter.nih.gov/v2/projects/search"
PAGE_LIMIT = 500
MAX_RETRIES = 3
SLEEP_SECONDS = 1


# NIH institute/center (IC) codes used for the `agency_ic_code`
# field when querying the NIH RePORTER projects API.
AGENCIES = [
    "AA",
    "AG",
    "AI",
    "AR",
    "AT",
    "CA",
    "CT",
    "DA",
    "DC",
    "DE",
    "DK",
    "EB",
    "ES",
    "EY",
    "GM",
    "HD",
    "HG",
    "HL",
    "LM",
    "MD",
    "MH",
    "NR",
    "NS",
    "OD",
    "RR",
    "TR",
    "TW",
]


def backoff(attempt):
    # Exponential base
    wait_time = 2**attempt

    # Add random "jitter" (between 0 and 1 second)
    jitter = random.uniform(0, 1)

    return wait_time + jitter


def fetch_projects(payload: dict) -> dict:
    resp = requests.post(API_URL, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def build_payload(
    fiscal_year: int, agency: str, offset: int, search_id: str | None
) -> dict:
    # Build the payload for the API request
    if search_id:
        return {"search_id": search_id, "offset": offset, "limit": PAGE_LIMIT}
    else:
        return {
            "criteria": {
                "use_relevance": False,
                "fiscal_years": [fiscal_year],
                "include_active_projects": False,
                "project_num_split": {
                    "ic_code": agency,
                },
                "exclude_subprojects": False,
                "multi_pi_only": False,
                "newly_added_projects_only": False,
                "sub_project_only": False,
            },
            "offset": offset,
            "limit": PAGE_LIMIT,
            "sort_field": "",
            "sort_order": "",
        }
