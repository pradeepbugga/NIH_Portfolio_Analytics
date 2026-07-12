#main.py

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import json
import os
import time
from typing import List, Dict, Any, Optional

import anyio
from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request, HTTPException, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

import pandas as pd

from core.db.connection import get_db_connection
from core.services.formatting import extract_funding, extract_ontology_distribution, format_output_grants

from app.startup import GLOBAL_AGENCIES_LIST, GLOBAL_VALID_ACTIVITY_CODES, GLOBAL_SYNONYM_REGISTRY, application_lifespan
from core.services.search_services import search
from core.services.activity_service import get_activity_portfolio
from core.services.agency_service import get_agency_portfolio

from core.search.search_service_prod import hybrid_search_range
from core.search.cache import get_cached_results, save_cached_results
from core.search.query_embedding import warmup_query_encoder, embed_query
from core.search.modal_reranker import distributed_rerank_fn
from core.search.combine import combine_and_sort_semantic_filter
from core.search.candidate_retrieval import retrieve_candidates_range_portfolio
from core.search.load_docs import load_grant_texts
from core.cluster.load_embeddings_text import load_grant_embeddings_and_text
from core.category.mapping import category_mapping, machine_human_map


load_dotenv()


# ===============================================================
# FRAMEWORK INITIALIZATION AND ROUTER SETUP
# ===============================================================
app = FastAPI(title="NIH Grant Search API", lifespan=application_lifespan)

app.mount("/static", StaticFiles(directory="./app/static"), name="static")
templates = Jinja2Templates(directory="./app/templates")

# ===============================================================
# API APPLICATION CORE ENDPOINTS
# ===============================================================
@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    """
    Renders the home page with a search bar and agency/activity code filters.

    Parameters
    ----------
    request : Request
        The FastAPI request object, used to pass context to the template.
    
    Returns
    -------
    TemplateResponse
        A Jinja2 template response rendering the home page with the search bar and filters.
    """


    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "agencies": GLOBAL_AGENCIES_LIST,
            "valid_activity_codes": GLOBAL_VALID_ACTIVITY_CODES
        }
    )

@app.get("/portfolio")
def portfolio_page(request: Request):

    """
    Renders the portfolio page (global analysis of NIH grants).

    Parameters
    ----------
    request : Request
        The FastAPI request object, used to pass context to the template.
    
    Returns
    -------
    TemplateResponse
        A Jinja2 template response rendering the portfolio page.
    """

    return templates.TemplateResponse(
        "portfolio.html",
        {"request": request}
    )

@app.get("/categories")
def categories_page(request: Request):

    """
    Renders the categories page (look-up table for category definitions).
    
    Parameters
    ----------
    request : Request
        The FastAPI request object, used to pass context to the template.   

    Returns
    -------
    TemplateResponse
        A Jinja2 template response rendering the categories page.
    
    """
    return templates.TemplateResponse(
        "categories.html",
        {"request": request}
    )


@app.get("/contact_us")
def contact_page(request: Request):

    """
    Renders the contact us page for user inquiries.

    Parameters
    ----------
    request : Request
        The FastAPI request object, used to pass context to the template.
    
    Returns
    -------
    TemplateResponse
        A Jinja2 template response rendering the contact us page.
    """

    return templates.TemplateResponse(
        "contact_us.html",
        {"request": request}
    )

@app.get("/search")
async def search(request: Request,
    query: str = Query(..., description="Search query string")):

    """
    Handles the search endpoint, performing a hybrid search over NIH grant documents.

    Parameters
    ----------

    request : Request
        The FastAPI request object, used to pass context to the template.
    query : str
        The search query string provided by the user.   

    Returns
    -------
    TemplateResponse
        A Jinja2 template response rendering the search results page with ranked grants and visualizations.
    """

    context = await search(request, query, rerank_fn=distributed_rerank_fn, synonym_registry=GLOBAL_SYNONYM_REGISTRY)

    context["request"] = request

    return templates.TemplateResponse(
        "results.html",
        context
    )

   

@app.get("/activity_codes", response_class=HTMLResponse)
async def activity_codes_multi_search(
    request: Request, 
    codes: str = Query(..., description="Comma-separated 3-character NIH Activity codes")
):

    """
    Handles the activity codes search endpoint, retrieving and aggregating grants based on a list of NIH activity codes.

    Parameters
    ----------
    request : Request
        The FastAPI request object, used to pass context to the template.
    codes : str
        A comma-separated string of NIH activity codes (e.g., "R01,R21,R03") to filter grants by.

    Returns
    -------
    TemplateResponse
        A Jinja2 template response rendering the search results page with ranked grants and visualizations for the specified activity codes.
    """
    
    context = await get_activity_portfolio(codes, code_registry = GLOBAL_VALID_ACTIVITY_CODES)

    context["request"] = request

    return templates.TemplateResponse(
        "results.html",
        context
    )




@app.get("/agency/{agency_code}", response_class=HTMLResponse)
async def agency_portal(request: Request, agency_code: str):

    """
    Handles the agency portal endpoint, retrieving and aggregating grants based on a specific NIH agency code.

    Parameters
    ----------
    request : Request
        The FastAPI request object, used to pass context to the template.

    agency_code : str
        The NIH agency code (e.g., "NCI", "NIAID") to filter grants by.

    Returns
    -------
    TemplateResponse
        A Jinja2 template response rendering the search results page with ranked grants and visualizations for the specified agency.
    """

    context = await get_agency_portfolio(agency_code, code_registry = GLOBAL_AGENCIES_LIST)

    context["request"] = request

    return templates.TemplateResponse(
        "results.html",
        context
    )



@app.get("/api/portfolio/categories")
async def portfolio_categories(year: int = Query(..., description="Target fiscal year for categorization analysis")):
    
    context = await get_category_distribution(year)

    return context


@app.get("/api/portfolio/grants")
async def portfolio_grants(
    year: int = Query(..., description="Target fiscal year for grant retrieval"),
    category: str = Query(..., description="Target abstract category for grant retrieval")
):
    """
    API endpoint to retrieve a list of grants for a given fiscal year and abstract category.
    """

    # 1. Strict validation dictionary map for dynamic SQL column selection based on category
    category_columns = {
        "mechanistic": "mechanistic",
        "therapeutic": "therapeutic",
        "diagnostic": "diagnostic",
        "research_tool": "research_tool",
        "clinical": "clinical",
        "infrastructure": "infrastructure",
        "education": "education",
        "obs_ep": "obs_ep"
    }   

    if category not in category_columns:
        raise HTTPException(status_code=400, detail="Invalid category specified.")

    column = category_columns[category]

    # 2. Database connection and query execution
    def fetch_grants_by_category():
        
        conn = get_db_connection()
        cur = conn.cursor()

        try:
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
                grants.append({
                    "grant_id": row[0],
                    "title": row[1],
                    "organization": row[2],
                    "pi": row[3],
                    "funding": row[4],
                    "agency_ic": row[5],
                    "activity_code": row[6],
                    "summary": row[7]
                })
            return grants
        finally:
            cur.close()
            conn.close()
    
    # 3. Offload the database operation to a thread-safe context to avoid blocking the event loop
    try:
        grant_results = await anyio.to_thread.run(fetch_grants_by_category)
    except Exception as e:
        print(f"❌ Error fetching grants by category: {e}")
        raise HTTPException(status_code=500, detail="Database lookup error.")

    return {
        "category": category,
        "year": year,
        "grants": grants
    }


class SearchRequest(BaseModel):
    year: str
    category: Optional[str] = None
    query: str
    existing_ids: List[str] # Validated as a native array of strings
    query_history_count: int = 1  # use this to track queries to then route to either semantic or hybrid search
 

@app.post("/api/portfolio/grants/search")
async def portfolio_grants_search(payload: SearchRequest):
    """
    API endpoint to perform a semantic search filter over a predefined set of grants
    """
    print("\n" + "="*50)
    print("=== INCOMING BACKEND SEARCH REQUEST ===")
    print(f"Payload Year: {payload.year} (Type: {type(payload.year)})")
    print(f"Payload Category: {payload.category}")
    print(f"Payload Query Term: '{payload.query}'")
    print(f"Payload Query History Count: {payload.query_history_count}")
    print(f"Incoming existing_ids length: {len(payload.existing_ids) if payload.existing_ids else 0}")
    print("="*50 + "\n")

    category_columns = {
        "mechanistic": "mechanistic",
        "therapeutic": "therapeutic",
        "diagnostic": "diagnostic",
        "research_tool": "research_tool",
        "clinical": "clinical",
        "infrastructure": "infrastructure",
        "education": "education",
        "obs_ep": "obs_ep"
    }

    column = None
    if payload.category:
        if payload.category not in category_columns:
            raise HTTPException(status_code=400, detail="Invalid category")
        column = category_columns[payload.category]


    # dynamic search routing to look up initial candidate IDs
    def determine_allowed_grants():
        
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Determine pool of grants to search
            if payload.existing_ids:
                return [str(x).strip() for x in payload.existing_ids if x], cur, conn
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
            
            return [row[0] for row in cur.fetchall()], cur, conn
        except Exception:
            cur.close()
            conn.close()
            raise

    try:
        allowed_grant_ids, cur, conn = await anyio.to_thread.run(determine_allowed_grants)
    except Exception as e:
        print(f"❌ Error determining allowed grants: {e}")
        raise HTTPException(status_code=500, detail="Database lookup error.")

    try:
        is_nested_subsearch = payload.query_history_count > 1

        # ROUTE 1: HYBRID SEARCH (Semantic + Substring Filter) for nested sub-searches
        if is_nested_subsearch and allowed_grant_ids:
            print("🔍 Routing to HYBRID SEARCH (Semantic + Substring Filter)")

            def run_hybrid_search():

                keyword_escaped = f"%{payload.query.strip()}%"
                keyword_sql = """
                    SELECT rg.grant_id
                    FROM ResearchGrants rg
                    LEFT JOIN Grant_Summaries s ON rg.grant_id = s.grant_id
                    WHERE rg.grant_id in %s
                    AND (rg.project_title ILIKE %s OR s.two_sentence_summary ILIKE %s or rg.abstract ILIKE %s)
                """
                cur.execute(keyword_sql, (tuple(allowed_grant_ids), keyword_escaped, keyword_escaped, keyword_escaped))
                keyword_matches = [row[0] for row in cur.fetchall()]

                if keyword_matches:
                    docs = load_grant_texts(cur, keyword_matches)
                    for d in docs:
                        d["vector_similarity"] = 1.0
                    return docs
                return []

            docs = await anyio.to_thread.run(run_hybrid_search)

            if docs:
                docs_text = [d["text"] for d in docs]
                # async remote call to the rerank function for scoring
                scores = await rerank_fn.remote.aio(payload.query, docs_text)

                def process_hybrid_ranking():
                    ranked = combine_and_sort_semantic_filter(docs, scores)
                    return format_output_grants(ranked)

                formatted_grants = await anyio.to_thread.run(process_hybrid_ranking)
                return {
                    "query": payload.query,
                    "category": payload.category,
                    "year": payload.year,
                    "grants": formatted_grants
                }
            else:
                print("ℹ️ Hybrid text search returned 0 matches within subset.")
                return {
                    "query": payload.query,
                    "category": payload.category,
                    "year": payload.year,
                    "grants": []
                }

        # ROUTE 2: FALLBACK / PURE SEMANTIC SEARCH for first-level queries or when no existing_ids are provided
        print("🎯 Routing to PURE SEMANTIC VECTOR SEARCH")
        
        # Guard against running a vector search over an completely empty ID filter block
        if not allowed_grant_ids:
            return {
                "query": payload.query,
                "category": payload.category,
                "year": payload.year,
                "grants": []
            }

        # Offload the vector embedding and retrieval to a thread-safe context to avoid blocking the event loop
        query_vec = await anyio.to_thread.run_sync(embed_query, payload.query)
        query_vec_list = query_vec.tolist()

        def run_vector_pipeline():
            candidates = retrieve_candidates_range_portfolio(
                cur,
                query_vec_list = query_vec_list,
                similarity_threshold = 0.25,
                allowed_grant_ids = allowed_grant_ids
                
            )

            vector_sim_map = {gid: sim for gid, sim in candidates}
            grant_ids = list(vector_sim_map.keys())

            if not grant_ids:
                return [], {}
            
            docs = load_grant_texts(cur, grant_ids)
            for d in docs:
                d["vector_similarity"] = vector_sim_map.get(d["grant_id"], 0.0)
            return docs, vector_sim_map

        docs, vector_sim_map = await anyio.to_thread.run(run_vector_pipeline)

        if not docs:
            return {
                "query": payload.query,
                "category": payload.category,
                "year": payload.year,
                "grants": []
            }

        doc_texts = [d["text"] for d in docs]
        # Async remote call to the rerank function for scoring
        scores = await rerank_fn.remote.aio(payload.query, doc_texts)

        def finalize_ranking():
            ranked = combine_and_sort_semantic_filter(docs, scores)
            return format_output_grants(ranked) 

        formatted_grants = await anyio.to_thread.run(finalize_ranking)

        return {
            "query": payload.query,
            "category": payload.category,
            "year": payload.year,
            "grants": formatted_grants
        }

    except Exception as e:
        print(f"❌ CRITICAL ENDPOINT FAILURE: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search pipeline execution failed: {str(e)}")

    finally:
        await anyio.to_thread.run(cur.close)
        await anyio.to_thread.run(conn.close)


@app.get("/api/grant/{grant_id}/abstract")
async def get_grant_abstract(grant_id: str):
    """
    API endpoint to retrieve the abstract for a specific grant by its ID.
    """

    def fetch_abstract():
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT abstract
                FROM ResearchGrants
                WHERE grant_id = %s
            """, (grant_id,))

            return cur.fetchone()
        finally:
            cur.close()
            conn.close()
    
    try: 
        row = await anyio.to_thread.run(fetch_abstract)
    except Exception as e:
        print(f"❌ Error fetching abstract for grant {grant_id}: {e}")
        raise HTTPException(status_code=500, detail="Database lookup error.")
    
    if not row:
        raise HTTPException(status_code=404, detail="Grant not found.")

    return {"abstract": row[0] if row[0] else "No abstract available for this record."}
    