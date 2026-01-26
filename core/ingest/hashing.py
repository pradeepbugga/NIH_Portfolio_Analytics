#hashing.py
#this script contains functions to compute and check content hashes for NIH grant data

import hashlib, json

def content_hash(result: dict) -> str:
    payload = {
        "title": result.get("project_title") or "",
        "abstract": result.get("abstract_text") or "",
        "phr": result.get("phr_text") or "",
        "award": float(result.get("award_amount") or 0),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

def check_hash(cur, result: dict):
    
    project_num = result.get("project_num")
    sub_id = result.get("subproject_id")
    grant_id = f"{project_num}-{sub_id}" if sub_id else project_num
    

    cur.execute("""
        SELECT content_hash, record_version 
        FROM ResearchGrants 
        WHERE grant_id = %s
        """, 
        (grant_id,)
    )
    row = cur.fetchone()
    return grant_id, row