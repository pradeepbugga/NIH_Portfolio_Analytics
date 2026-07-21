from core.ingest.hashing import compute_content_hash, fetch_existing_hash
from core.ingest.persistence import (
    insert_organization,
    insert_research_grant,
    update_research_grant,
    insert_pis,
    update_grant_embeddings,
)
from core.ingest.normalize import normalize_project_num
from core.ingest.org_resolution import resolve_org


def process_result(
    result: dict, cur, org_cache: dict, ingest_id: str, policy: dict, metrics: dict
):
    """
    Process a single NIH grant result, resolve the organization, compute the content hash, and insert or update the record in the database.

    Parameters
    ----------
    result (dict): A dictionary containing NIH grant data.
    cur: A database cursor for executing SQL queries.
    org_cache (dict): A cache of organization information to avoid redundant API calls.
    ingest_id (str): A unique identifier for the current ingestion process.
    policy (dict): A dictionary containing policy settings for organization resolution.
    metrics (dict): A dictionary to track metrics such as the number of inserted, updated, skipped, and errored records.

    Raises
    ------
    ValueError: If the organization cannot be resolved for the given grant.
    """

    # populate hash for record integrity
    new_hash = compute_content_hash(result)
    grant_id, existing_hash = fetch_existing_hash(cur, result)

    # Resolve organization
    # ---------------

    coreprojectnum = normalize_project_num(result.get("project_num"))

    org, status = resolve_org(
        cur=cur,
        core_project_num=coreprojectnum,
        fiscal_year=result.get("fiscal_year"),
        organization=result.get("organization", {}),
        agency_abbr=result.get("agency_ic_admin", {}).get("abbreviation", ""),
        cache=org_cache,
        policy=policy,
    )

    if not org:
        raise ValueError(f"Could not resolve organization for grant {grant_id}")

    org_id = insert_organization(cur, org)
    record_changed = False

    # ---------------------
    # Based on hash check, insert or skip research grant
    # ---------------------

    # if no existing record, insert
    if existing_hash is None:
        insert_research_grant(
            cur=cur,
            result=result,
            core_project_num=coreprojectnum,
            org_id=org_id,
            org_resolution_status=status,
            ingest_id=ingest_id,
            compute_content_hash=new_hash,
        )
        record_changed = True
        metrics["num_inserted"] += 1
    # if the hash matches, skip

    elif existing_hash[0] == new_hash:
        metrics["num_skipped"] += 1
        return

    # if the hash is different, update
    else:
        old_version = existing_hash[1]
        update_research_grant(
            cur=cur,
            result=result,
            grant_id=grant_id,
            ingest_id=ingest_id,
            compute_content_hash=new_hash,
            record_version=old_version,
        )
        update_grant_embeddings(cur, grant_id)
        record_changed = True
        metrics["num_updated"] += 1

    # Insert principal investigators
    if record_changed:
        insert_pis(cur, grant_id, result.get("principal_investigators", []))
