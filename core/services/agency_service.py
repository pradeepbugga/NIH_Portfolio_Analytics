import anyio

import time
import logging

from core.db.connection import get_db_connection
from core.constants import ONTOLOGY_LABELS

logger = logging.getLogger(__name__)


async def get_agency_portfolio(agency_code: str, code_registry: list[dict]) -> dict:

    """
    Retrieves the portfolio of grants for a specific agency code.
    Includes historical funding trends, ontology distribution, and detailed grant information.

    Parameters
    ----------
    agency_code : str
        The agency code to filter the grants by.
    code_registry : list[dict]
        A list of dictionaries containing valid agency codes and their associated metadata.
    
    Returns
    -------
    dict
        A dictionary containing the aggregated results, including:
        - ``query``: a string representation of the agency code.
        - ``years``: a list of fiscal years for which data is available.
        - ``funding``: a list of total funding amounts corresponding to each fiscal year.
        - ``results``: a list of detailed grant records for the specified agency code.
        - ``ontology_labels``: a list of ontology category labels.
        - ``ontology_values``: a list of total funding amounts corresponding to each ontology category.

    Raises
    ------
    ValueError
        If the agency_code is empty or not found in the code_registry.
    Exception
        If there is an error during database operations.
    """

    target_code = agency_code.upper()

    logger.info("Retrieving portfolio for agency code: %s", target_code)

    start = time.perf_counter()

    conn = await anyio.to_thread.run_sync(get_db_connection)
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

            ontology_values = (
                [float(val) for val in onto_row] if onto_row else [0.0] * 8
            )

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

            grants = []
            for row in rows:
                grants.append(
                    {
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
                        "summary": row[16],
                    }
                )

            return years, funding, ontology_values, grants

        finally:
            cur.close()
            conn.close()

    try:
        years, funding, ontology_values, grants = await anyio.to_thread.run_sync(
            run_agency_filtering
        )

    except Exception:
        logger.exception(
            "Failed to retrieve agency portfolio for code: %s", target_code
        )
        raise

    display_title = f"Agency Portfolio: {target_code}"

    for agency in code_registry:
        if agency.get("funding_code") == target_code:
            display_title = agency.get("abbreviation", display_title)
            break

    logger.info(
        "Retrieved %d grants for agency code: %s in %.2f seconds",
        len(grants),
        target_code,
        time.perf_counter() - start,
    )

    return {
        "query": display_title,
        "years": years,
        "funding": funding,
        "results": grants,
        "ontology_labels": ONTOLOGY_LABELS,
        "ontology_values": ontology_values,
    }
