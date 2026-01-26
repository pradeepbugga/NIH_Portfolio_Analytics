# combine.py
# this script combines reranker scores with document metadata and returns sorted results

MIN_SCORE_THRESHOLD = -2.0


def combine_and_sort(docs, scores):
    
    assert len(docs) == len(scores)

    results = []
    for doc, score in zip(docs, scores):
        if score > MIN_SCORE_THRESHOLD:
            results.append({
                "grant_id": doc["grant_id"],
                "title": doc["title"],
                "subproject_id": doc["subproject_id"],
                "core_project_num": doc["core_project_num"],
                "fiscal_year": doc["fiscal_year"],
                "amount": doc["amount"],
                "abstract": doc["abstract"],
                "phr": doc["phr"],
                "agency_ic": doc["agency_ic"],
                "project_start_date": doc["project_start_date"],
                "project_end_date": doc["project_end_date"],
                "budget_start_date": doc["budget_start_date"],
                "budget_end_date": doc["budget_end_date"],
                "org_name": doc["org_name"],
                "org_city": doc["org_city"],
                "org_state": doc["org_state"],
                "org_country": doc["org_country"],
                "pi_first_name": doc["pi_first_name"],
                "pi_middle_name": doc["pi_middle_name"],

                "vector_similarity": doc.get("vector_similarity", 0.0)
            })
        
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

