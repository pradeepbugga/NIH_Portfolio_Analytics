import time
import anyio
from fastapi import HTTPException
from core.db import get_db_connection

from core.consants import ONTOLOGY_LABELS


async def get_agency_portfolio(agency_code: str):

    target_code = agency_code.upper()

    conn = await anyio.to_thread.run(get_db_connection)
    cur = conn.cursor()

    def run_agency_filtering():

        try: 
            # STEP 1: HISTORICAL DATA FOR CHARTS 
            timeline_query = """
                SELECT fiscal_year, SUM(total_award_amount)
                FROM ResearchGrants
                WHERE agency_code = %s
                GROUP BY fiscal_year
                ORDER BY fiscal_year ASC;
            """
            cur.execute(timeline_query, (target_code,))
            timeline_rows = cur.fetchall()

            years = [row[0] for row in timeline_rows]
            funding = [float(row[1]) if row[1] else 0.0 for row in timeline_rows]

            # STEP 2: CATEGORY DISTRIBUTION AGGREGATION (Ontology Labels)
            
            ontology_query = """
                SELECT               
                    COALESCE(SUM(CASE WHEN gl.mechanistic = 1 THEN rg.total_award_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN gl.therapeutic = 1 THEN rg.total_award_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN gl.diagnostic = 1 THEN rg.total_award_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN gl.research_tool = 1 THEN rg.total_award_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN gl.clinical = 1 THEN rg.total_award_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN gl.infrastructure = 1 THEN rg.total_award_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN gl.education = 1 THEN rg.total_award_amount ELSE 0 END), 0),
                    COALESCE(SUM(CASE WHEN gl.obs_ep = 1 THEN rg.total_award_amount ELSE 0 END), 0)
                FROM ResearchGrants rg
                INNER JOIN grant_labels gl ON rg.grant_id = gl.grant_id
                WHERE rg.agency_code = %s;
            """
            cur.execute(ontology_query, (target_code,))
            onto_row = cur.fetchone()

            ontology_values = [float(val) for val in onto_row] if onto_row else [0.0] * 8

            # STEP 3: TABLE REVIEWS (2025 Viewport Only) - Fetch all grants for the agency in 2025
            
            table_query = """
                SELECT
                    rg.grant_id,
                    rg.project_title,
                    o.name AS organization,
                    rg.contact_pi_id,
                    rg.total_award_amount,
                    rg.agency_ic,                
                    rg.fiscal_year,
                    gl.mechanistic,
                    gl.therapeutic,
                    gl.diagnostic,
                    gl.research_tool,
                    gl.clinical,
                    gl.infrastructure,
                    gl.education,
                    gl.obs_ep,
                    rg.activity_code,
                    s.two_sentence_summary AS summary_text
                FROM ResearchGrants rg
                JOIN grant_labels gl ON rg.grant_id = gl.grant_id
                INNER JOIN Grant_Summaries s ON rg.grant_id = s.grant_id
                LEFT JOIN organizations o ON rg.organization_id = o.id
                WHERE 
                    rg.agency_code = %s 
                    AND rg.fiscal_year = 2025 -- ✨ Keep memory completely flat
                ORDER BY rg.total_award_amount DESC;
            """
            cur.execute(table_query, (target_code,))
            rows = cur.fetchall()
            print(f"⏱️ DB 2025 Table Query took: {time.time() - t_start:.4f}s")

            grants = []
            for row in rows:
                grants.append({
                    "grant_id": row[0],
                    "title": row[1],
                    "organization": row[2] if row[2] else "Unknown Institution",
                    "pi": row[3],
                    "amount": float(row[4]) if row[4] else 0.0,
                    "agency_ic": row[5],
                    "fiscal_year": int(row[6]) if row[6] else 2025,                
                    "mechanistic": row[7],
                    "therapeutic": row[8],
                    "diagnostic": row[9],
                    "research_tool": row[10],
                    "clinical": row[11],
                    "infrastructure": row[12],
                    "education": row[13],
                    "obs_ep": row[14],
                    "activity_code": row[15],
                    "summary": row[16]
                })

            return years, funding, ontology_values, grants

        finally:
            cur.close()
            conn.close()

    try:
        years, funding, ontology_values, grants = await anyio.to_thread.run(run_agency_filtering)
    except Exception as e:
        print(f"❌ Error in agency_portal route: {e}")
        raise HTTPException(status_code=500, detail="Database lookup error.")

    display_title = f"Agency Portfolio: {target_code}"
    
    for agency in GLOBAL_AGENCIES_LIST:
        if agency.get("funding_code") == target_code:
            display_title = agency.get("abbreviation", display_title)
            break


    return {
            "query": display_title,
            "years": years,
            "funding": funding,
            "results": grants, # Populates the 2025 UI data table view flawlessly
            "ontology_labels": ONTOLOGY_LABELS, 
            "ontology_values": ontology_values
        }
    
