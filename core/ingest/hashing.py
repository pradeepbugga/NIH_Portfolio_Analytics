import hashlib, json

def compute_content_hash(result: dict) -> str:

    """
    Compute the SHA-256 content hash for a given NIH grant result.

    Parameters
    ----------
    result (dict): A dictionary containing NIH grant data, including 'project_title', 'abstract', 'phr', and 'award_amount'.

    Returns
    -------
    str: The computed SHA-256 content hash as a hexadecimal string.
    """

    payload = {
        "title": result.get("project_title") or "",
        "abstract": result.get("abstract_text") or "",
        "phr": result.get("phr_text") or "",
        "award": float(result.get("award_amount") or 0),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

def fetch_existing_hash(cur, result: dict):

    """
    Fetch the existing content hash and record version for a given NIH grant result from the database.

    Parameters
    ----------
    cur: A database cursor for executing SQL queries.
    result (dict): A dictionary containing NIH grant data, including 'project_num' and 'subproject_id'.

    Returns
    -------
    tuple: A tuple containing the grant ID, existing content hash, and record version. If the grant does not exist in the database, returns (grant_id, None).
    """

   
    project_num = result.get("project_num")
    sub_id = result.get("subproject_id")
    grant_id = (
        f"{project_num}-{sub_id}"
        if sub_id not in (None, "")
        else project_num
    )
    

    cur.execute("""
        SELECT content_hash, record_version 
        FROM ResearchGrants 
        WHERE grant_id = %s
        """, 
        (grant_id,)
    )
    row = cur.fetchone()
    return grant_id, row