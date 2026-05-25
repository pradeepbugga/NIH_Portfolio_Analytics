# this script fetches grant texts and metadata from the database for reranking
# order of grant_ids is preserved in the returned list

# we make sure to retrieve all SQL fields

def load_grant_texts(cur, grant_ids):
   
    if not grant_ids:
        return []

    cur.execute(
        """
        SELECT
            rg.grant_id,
            rg.project_title,
            rg.subproject_id,
            rg.abstract,
            rg.core_project_num,
            rg.fiscal_year,
            rg.total_award_amount,
            rg.phr,
            rg.agency_ic,
            rg.activity_code,
            rg.project_start_date,
            rg.project_end_date,
            rg.budget_start_date,
            rg.budget_end_date,
            o.name,
            o.city,
            o.state,
            o.country,
            p.first_name,
            p.middle_name,
            p.last_name,
            gl.mechanistic,
            gl.diagnostic,
            gl.therapeutic,
            gl.research_tool,
            gl.clinical,
            gl.infrastructure,
            gl.education,
            gl.obs_ep,
            s.two_sentence_summary AS summary_text            
        FROM ResearchGrants rg
        LEFT JOIN rgrantpis rgp
            ON rg.grant_id = rgp.grant_id
            AND rgp.is_contact_pi = TRUE
        LEFT JOIN PIs p 
            ON rgp.pi_id = p.id
        INNER JOIN Grant_Summaries s ON rg.grant_id = s.grant_id
        LEFT JOIN Organizations o on rg.organization_id = o.id
        LEFT JOIN grant_labels gl on rg.grant_id = gl.grant_id
        WHERE rg.grant_id = ANY(%s)
        """,
        (grant_ids,)
    )

    rows = cur.fetchall()
    row_map = {r[0]: r for r in rows}

    docs = []
    for gid in grant_ids:
        if gid not in row_map:
            continue

        (_, title, subproject_id, abstract, core, fy, amount, phr, agency_ic, activity_code,
        project_start_date, project_end_date, budget_start_date, budget_end_date, 
        org_name, org_city, org_state, org_country, pi_first_name, pi_middle_name, 
        pi_last_name, mechanistic, diagnostic, therapeutic, research_tool, clinical, infrastructure, education, obs_ep, summary_text) = row_map[gid]

        doc_text = f"{(title or '').strip()} {(abstract or '').strip()}"

        docs.append({
            "grant_id": gid,
            "title": title,
            "subproject_id": subproject_id,
            "abstract": abstract,
            "phr": phr,
            "agency_ic": agency_ic,
            "activity_code": activity_code,
            "project_start_date": project_start_date,
            "project_end_date": project_end_date,
            "budget_start_date": budget_start_date,
            "budget_end_date": budget_end_date,
            "org_name": org_name,
            "org_city": org_city,
            "org_state": org_state,
            "org_country": org_country,
            "pi_first_name": pi_first_name,
            "pi_middle_name": pi_middle_name,
            "pi_last_name": pi_last_name,
            "core_project_num": core,
            "fiscal_year": fy,
            "amount": amount,
            "text": doc_text,
            "mechanistic": mechanistic,
            "diagnostic": diagnostic,
            "therapeutic": therapeutic,
            "research_tool": research_tool,
            "clinical": clinical,
            "infrastructure": infrastructure,
            "education": education,
            "obs_ep": obs_ep,
            "summary": summary_text
        })

    return docs