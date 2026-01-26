
# this script contains functions to process NIH grant data and insert or update it in the database

from core.ingest.hashing import content_hash, check_hash
from core.ingest.persistence import insert_organization, insert_research_grant, update_research_grant, insert_pis, update_grant_embeddings
from core.ingest.normalize import normalize_project_num
from core.ingest.org_resolution import resolve_org


def process_result(result: dict, cur, org_cache: dict, ingest_id: str, policy: dict, metrics: dict):
        
    #populate hash for record integrity
    hash_result = content_hash(result)
    grant_id, hash_check = check_hash(cur, result)
    
    
    # Resolve organization  
    # --------------- 
      
    coreprojectnum = normalize_project_num(result.get("project_num"))

   
    org, status = resolve_org(cur=cur, core_project_num=coreprojectnum,
                      fiscal_year=result.get('fiscal_year'),
                      organization=result.get('organization', {}),
                      agency_abbr=result.get("agency_ic_admin", {}).get("abbreviation", ""),
                      cache=org_cache,
                      policy=policy)
    

    if not org:
        raise ValueError(f"Could not resolve organization for grant {grant_id}")

    org_id = insert_organization(cur, org)
    changed = False

    #---------------------
    # Based on hash check, insert or skip research grant
    #---------------------

    # if no existing record, insert
    if hash_check is None:
        insert_research_grant(cur=cur, result=result, core_project_num=coreprojectnum, org_id=org_id, org_resolution_status=status, ingest_id=ingest_id, content_hash=hash_result)
        changed = True
        metrics["num_inserted"] += 1
    # if the hash matches, skip
    elif hash_check[0] == hash_result:
        metrics["num_skipped"] += 1
        return
    # if the hash is different, update    
    else:
        old_version = hash_check[1]
        update_research_grant(cur=cur, result=result, grant_id=grant_id, ingest_id=ingest_id, content_hash=hash_result, record_version=old_version)
        update_grant_embeddings(cur, grant_id)
        changed = True
        metrics["num_updated"] += 1


    # Insert principal investigators
    if changed:
        insert_pis(cur, grant_id, result.get('principal_investigators', []))
  

