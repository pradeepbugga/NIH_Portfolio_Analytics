import anyio

import logging

from core.db.connection import get_db_connection
from core.constants import ONTOLOGY_LABELS
from core.search.constants import VALID_CATEGORY_COLUMNS

from core.search.query_embedding import embed_query
from core.search.candidate_retrieval import retrieve_candidates_range_portfolio
from core.search.load_docs import load_grant_texts
from core.search.combine import combine_and_sort_semantic_filter
from core.services.formatting import format_output_grants

from pydantic import BaseModel, Field
from typing import List, Optional

logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    year: int
    category: Optional[str] = None
    query: str
    existing_ids: List[str] = Field(
        default_factory=list
    )  # Validated as a native array of strings
    query_history_count: int = (
        1  # use this to track queries to then route to either semantic or hybrid search
    )


async def get_category_distribution(year: int) -> dict:
    """
    Retrieves the total funding distribution across predefined ontology categories for a given fiscal year.
    FYI this does not show any grants, just the total funding distribution across the 8 abstract categories.

    Parameters
    ----------
    year : int
        The fiscal year for which to retrieve the funding distribution.

    Returns
    -------
    dict
        A dictionary mapping each ontology category label to its corresponding total funding amount for the specified fiscal year.
    """

    conn = await anyio.to_thread.run_sync(get_db_connection)
    cur = conn.cursor()

    try:

        def fetch_category_distribution():

            cur.execute(
                """
                SELECT

                    SUM(CASE WHEN gl.mechanistic = 1
                        THEN rg.total_award_amount ELSE 0 END),

                    SUM(CASE WHEN gl.therapeutic = 1
                        THEN rg.total_award_amount ELSE 0 END),

                    SUM(CASE WHEN gl.diagnostic = 1
                        THEN rg.total_award_amount ELSE 0 END),

                    SUM(CASE WHEN gl.research_tool = 1
                        THEN rg.total_award_amount ELSE 0 END),

                    SUM(CASE WHEN gl.clinical = 1
                        THEN rg.total_award_amount ELSE 0 END),

                    SUM(CASE WHEN gl.infrastructure = 1
                        THEN rg.total_award_amount ELSE 0 END),

                    SUM(CASE WHEN gl.education = 1
                        THEN rg.total_award_amount ELSE 0 END),

                    SUM(CASE WHEN gl.obs_ep = 1
                        THEN rg.total_award_amount ELSE 0 END)

                FROM grant_labels gl

                JOIN ResearchGrants rg
                    ON gl.grant_id = rg.grant_id

                WHERE rg.fiscal_year = %s
            """,
                (year,),
            )

            row = cur.fetchone()
            if not row:
                return [0] * 8
            return [val or 0 for val in row]

        values = await anyio.to_thread.run_sync(fetch_category_distribution)

        return dict(zip(ONTOLOGY_LABELS, values))

    finally:
        await anyio.to_thread.run_sync(cur.close)
        await anyio.to_thread.run_sync(conn.close)


async def get_grants_by_category(year: int, category: str) -> dict:
    """
    Retrieves grants for a specific fiscal year and abstract category, returning detailed grant information.

    Parameters
    ----------
    year : int
        The fiscal year for which to retrieve grants.
    category : str
        The abstract category for which to retrieve grants. Must be one of the valid categories defined in VALID_CATEGORY_COLUMNS.

    Returns
    -------
    dict
        A dictionary containing the following keys:
        - ``category``: The abstract category used for filtering.
        - ``year``: The fiscal year used for filtering.
        - ``grants``: A list of dictionaries, each containing detailed information about a grant, including:
            - ``grant_id``: The unique identifier of the grant.
            - ``title``: The title of the grant project.
            - ``organization``: The name of the organization receiving the grant.
            - ``pi``: The contact principal investigator's ID.
            - ``funding``: The total award amount for the grant.
            - ``agency_ic``: The agency or institute code associated with the grant.
            - ``activity_code``: The activity code associated with the grant.
            - ``summary``: A two-sentence summary of the grant project.

    Raises
    ------
    ValueError
        If the provided category is not in the list of valid categories defined in VALID_CATEGORY_COLUMNS.
    """

    logger.info("Retrieving grants for year %d and category '%s'", year, category)

    if category not in VALID_CATEGORY_COLUMNS:
        raise ValueError(f"Invalid category '{category}'")

    column = category  # Use the category directly as the column name

    conn = await anyio.to_thread.run_sync(get_db_connection)
    cur = conn.cursor()

    try:

        def fetch_grants_by_category():

            query = f"""
                SELECT
                    rg.grant_id,
                    rg.project_title,
                    o.name AS organization,
                    rg.contact_pi_id,
                    rg.total_award_amount,
                    rg.agency_ic,
                    rg.activity_code,
                    s.two_sentence_summary AS summary_text
                FROM ResearchGrants rg
                JOIN grant_labels gl
                    ON rg.grant_id = gl.grant_id
                INNER JOIN Grant_Summaries s ON rg.grant_id = s.grant_id
                LEFT JOIN organizations o
                    ON rg.organization_id = o.id
                WHERE
                    rg.fiscal_year = %s
                    AND gl.{column} = 1
                ORDER BY rg.total_award_amount DESC
            """
            cur.execute(query, (year,))
            rows = cur.fetchall()

            grants = []
            for row in rows:
                grants.append(
                    {
                        "grant_id": row[0],
                        "title": row[1],
                        "organization": row[2],
                        "pi": row[3],
                        "funding": row[4],
                        "agency_ic": row[5],
                        "activity_code": row[6],
                        "summary": row[7],
                    }
                )
            return grants

        grants = await anyio.to_thread.run_sync(fetch_grants_by_category)

        logger.info("Retrieved %d grants.", len(grants))

        return {"category": category, "year": year, "grants": grants}

    finally:
        await anyio.to_thread.run_sync(cur.close)
        await anyio.to_thread.run_sync(conn.close)


async def search_portfolio(payload: SearchRequest, rerank_fn) -> dict:
    """
    Perform a search over the portfolio of grants based on the provided search request payload.
    The grants will either route to a semantic search or a keyword search depending on the query history count.

    Parameters
    ----------
    payload : SearchRequest
        The search request payload containing the query, year, category, and any existing IDs.
    rerank_fn : callable
        A function to rerank the candidate grant documents based on the search query.

    Returns
    -------
    dict
        A dictionary containing the search results, including the query, category, year, and a list of grants that match the search criteria.
    """

    logger.info(
        "Portfolio search started: query='%s', category='%s', year=%d",
        payload.query,
        payload.category,
        payload.year,
    )

    if payload.category not in VALID_CATEGORY_COLUMNS:
        raise ValueError(f"Invalid category '{payload.category}'")

    column = payload.category  # Use the category directly as the column name

    conn = await anyio.to_thread.run_sync(get_db_connection)
    cur = conn.cursor()

    try:

        candidate_ids = await anyio.to_thread.run_sync(
            _determine_candidate_ids, payload, cur, column
        )

        logger.info("Candidate pool contains %d grants.", len(candidate_ids))

        if not candidate_ids:
            return {
                "query": payload.query,
                "category": payload.category,
                "year": payload.year,
                "grants": [],
            }

        is_nested_search = payload.query_history_count > 1

        if is_nested_search:

            logger.info("Performing keyword search for query: '%s'", payload.query)

            docs = await anyio.to_thread.run_sync(
                _run_subset_keyword_search, payload, cur, candidate_ids
            )

            logger.info("Retrieved %d candidate documents.", len(docs))

        else:

            logger.info("Performing semantic search for query: '%s'", payload.query)

            docs = await anyio.to_thread.run_sync(
                _run_subset_semantic_search, payload, cur, candidate_ids
            )

            logger.info("Retrieved %d candidate documents.", len(docs))

        formatted_grants = await _rerank_and_format(payload.query, docs, rerank_fn)

        logger.info("Returning %d ranked grants.", len(formatted_grants))

        return {
            "query": payload.query,
            "category": payload.category,
            "year": payload.year,
            "grants": formatted_grants,
        }

    except Exception:
        logger.exception(
            "Error occurred during portfolio search for query: '%s'", payload.query
        )
        raise

    finally:
        await anyio.to_thread.run_sync(cur.close)
        await anyio.to_thread.run_sync(conn.close)


def _determine_candidate_ids(
    payload: SearchRequest, cur, column: str = None
) -> list[str]:
    """
    Determine the pool of candidate grant IDs based on the search payload.
    This is useful for only looking a the grants active in the frontend search.

    Parameters
    ----------

    payload : SearchRequest
        The search request payload containing the year, category, and any existing IDs.
    cur : any
        The database cursor for executing SQL queries.
    column : str, optional
        The column name corresponding to the category, if provided. Defaults to None.

    Returns
    -------
    list
        A list of grant IDs that match the criteria specified in the payload.

    """

    # Determine pool of grants to search
    if payload.existing_ids:
        return [str(x).strip() for x in payload.existing_ids if x]
    if column:
        sql = f"""
            SELECT rg.grant_id
            FROM ResearchGrants rg
            JOIN grant_labels gl ON rg.grant_id = gl.grant_id
            WHERE rg.fiscal_year = %s AND gl.{column} = 1
        """
        cur.execute(sql, (int(payload.year),))
    else:
        sql = """
            SELECT grant_id
            FROM ResearchGrants
            WHERE fiscal_year = %s
        """
        cur.execute(sql, (int(payload.year),))

    return [row[0] for row in cur.fetchall()]


async def _run_subset_keyword_search(
    payload: SearchRequest, cur, allowed_grant_ids: list[str]
):
    """
    Perform a keyword search over a predefined set of grants based on the provided query.
    This retrieves candidates using a substring filter and treats them as perfect lexical matches.
    This is useful once semantic search has already filtered the topic and a subsequent semnantic search would not be appropriate.
    (i.e. when we filter for multiple sclerosis then search for "antibody" we want keyword search
    not grants semantically related to "antibody" that are not about multiple sclerosis)

    Parameters
    ----------
    payload : SearchRequest
        The search request payload containing the query and other relevant information.
    cur
        The database cursor for executing SQL queries.
      allowed_grant_ids : list[str]
        A list of grant IDs that are allowed for the search, serving as a filter.

    Returns
    -------
    list
        A list of documents (grants) that match the substring search criteria.
    """

    def retrieve():

        keyword = f"%{payload.query.strip()}%"

        cur.execute(
            """
            SELECT rg.grant_id
            FROM ResearchGrants rg
            LEFT JOIN Grant_Summaries s
                ON rg.grant_id = s.grant_id
            WHERE
                rg.grant_id IN %s
                AND (
                    rg.project_title ILIKE %s
                    OR s.two_sentence_summary ILIKE %s
                    OR rg.abstract ILIKE %s
                )
            """,
            (
                tuple(allowed_grant_ids),
                keyword,
                keyword,
                keyword,
            ),
        )

        grant_ids = [row[0] for row in cur.fetchall()]

        if not grant_ids:
            return []

        docs = load_grant_texts(cur, grant_ids)

        # Treat keyword matches as perfect lexical matches.
        for doc in docs:
            doc["vector_similarity"] = 1.0

        logger.info("Keyword search matched %d grants.", len(docs))

        return docs

    return await anyio.to_thread.run_sync(retrieve)


async def _run_subset_semantic_search(
    payload: SearchRequest, cur, allowed_grant_ids: list[str]
):
    """
    Perform a semantic search over a predefined set of grants based on the provided query.
    This retrieves candidates but does not perform any additional filtering or reranking.

    Parameters
    ----------
    payload : SearchRequest
        The search request payload containing the query and other relevant information.
    cur
        The database cursor for executing SQL queries.
    allowed_grant_ids : list[str]
        A list of grant IDs that are allowed for the search, serving as a filter.

    Returns
    -------
    list
        A list of documents (grants) that match the semantic search criteria, each with its associated vector similarity score.
    """

    query_vec = await anyio.to_thread.run_sync(
        embed_query,
        payload.query,
    )
    query_vec_list = query_vec.tolist()

    def retrieve():

        candidates = retrieve_candidates_range_portfolio(
            cur,
            query_vec_list=query_vec_list,
            similarity_threshold=0.25,
            allowed_grant_ids=allowed_grant_ids,
        )

        vector_sim_map = {grant_id: similarity for grant_id, similarity in candidates}

        grant_ids = list(vector_sim_map.keys())

        if not grant_ids:
            return []

        docs = load_grant_texts(cur, grant_ids)

        for doc in docs:
            doc["vector_similarity"] = vector_sim_map.get(
                doc["grant_id"],
                0.0,
            )

        return docs

    docs = await anyio.to_thread.run_sync(retrieve)

    logger.info(
        "Semantic retrieval returned %d candidates.",
        len(docs),
    )

    return docs


async def _rerank_and_format(query: str, docs: list[dict], rerank_fn) -> list[dict]:
    """
    Rerank candidate grant documents and format them for frontend display.

    Parameters
    ----------
    query
        User search query.
    docs
        Candidate grant documents returned from either semantic or keyword retrieval.

    Returns
    -------
    list[dict]
        Formatted grant records sorted by semantic relevance.
    """

    if not docs:
        return []

    doc_texts = [doc["text"] for doc in docs]

    # Score documents with the remote cross-encoder
    scores = await rerank_fn.remote.aio(query, doc_texts)

    def finalize():

        ranked = combine_and_sort_semantic_filter(
            docs,
            scores,
        )

        return format_output_grants(ranked)

    results = await anyio.to_thread.run_sync(finalize)

    logger.info("Reranked and formatted %d grants.", len(results))

    return results
