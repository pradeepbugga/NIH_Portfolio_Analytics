#main.py

from fastapi import FastAPI, Query, Request, HTTPException, APIRouter
from core.db.connection import get_db_connection
from core.search.search_service_prod import semantic_search_range
from core.search.cache import get_cached_results, save_cached_results
from core.search.query_embedding import warmup_query_encoder



from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from datetime import datetime
from core.search.modal_reranker import rerank_fn
from core.search.combine import combine_and_sort_semantic_filter
from core.search.query_embedding import embed_query
from core.search.candidate_retrieval import retrieve_candidates_range_portfolio
from core.search.load_docs import load_grant_texts
from core.cluster.agglomerative_clustering import cluster_filtered_grants_for_map
from core.cluster.load_embeddings_text import load_grant_embeddings_and_text
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from dotenv import load_dotenv
import os
from core.category.mapping import category_mapping, machine_human_map
import pandas as pd
import time
from core.synthesis_prompts.prompts import REDUCE_PROMPT_AGENCY, REDUCE_PROMPT_PROJECT_TYPE, TOPIC_PROMPT_REGISTRY, DEFAULT_PROMPT_REDUCE_TOPIC, REDUCE_PROMPT_GEOGRAPHY
from core.synthesis_prompts.prompts import REDUCE_PROMPT_CAREER_STAGE, REDUCE_PROMPT_CATEGORY
from core.synthesis_prompts.prompt_utils import lookup_mission_by_name, format_currency_short
import asyncio
import numpy as np
from collections import Counter
from sklearn.metrics.pairwise import cosine_distances
from core.summarize_portfolio.class_registry import AnalyticalLensStrategy, InstitutionalEquityStrategy



load_dotenv()

client = genai.Client()

app = FastAPI(title="NIH Grant Search API")

app.mount("/static", StaticFiles(directory="./app/static"), name="static")
templates = Jinja2Templates(directory="./app/templates")



def normalize_query(q: str) -> str:
    return " ".join(q.lower().split())


def extract_funding(results):
    yearly_totals = {}
    now = datetime.now()
    current_fy = now.year if now.month < 10 else now.year + 1
    months_elapsed = (now.month - 10) % 12 + 1
    scaling_factor = 12/months_elapsed

    print(f"Current fiscal year: {current_fy}, months elapsed: {months_elapsed}, scaling factor: {scaling_factor}")
    for r in results["records"]:
        yr = r["fiscal_year"]
        amt = r["amount"] or 0 
        yearly_totals[yr] = yearly_totals.get(yr, 0) + amt

    if current_fy in yearly_totals:
        yearly_totals[current_fy] *= scaling_factor
    years = sorted(yearly_totals.keys())

    funding = [yearly_totals[yr] for yr in years]

    return years, funding

@app.get("/")
def home_page(request: Request):
    agencies_list = []
    
    # 1. This points to root/app/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Step UP out of 'app' into 'root', then down into 'core/agency' ✨
    csv_path = os.path.abspath(os.path.join(script_dir, "..", "core", "agency", "agencies_updated.csv"))

    print(f"DEBUG: Actively mapping to dataset pipeline at: {csv_path}")

    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            df = df.fillna("")
            df_sorted = df.sort_values(by="agency_ic")
            agencies_list = df_sorted.to_dict(orient="records")
            print(f"✅ SUCCESS: Connected path. Injecting {len(agencies_list)} rows.")
        except Exception as e:
            print(f"❌ ERROR reading/parsing CSV layout matrix: {e}")
    else:
        print(f"❌ CRITICAL FAILURE: Could not find your file at: {csv_path}")


    # now load activity codes
    activity_csv_path = os.path.abspath(os.path.join(script_dir, "..", "core", "activity_codes", "2025_code_list.csv"))

    if os.path.exists(activity_csv_path):
        try:
            df_activity = pd.read_csv(activity_csv_path)
            valid_activity_codes = df_activity["Activity_Code"].str.upper().tolist()
            print(f"✅ SUCCESS: Connected to activity codes dataset. Found {len(activity_codes_list)} codes.")
        except Exception as e:
            print(f"❌ ERROR reading/parsing activity codes CSV: {e}")


    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "agencies": agencies_list,
            "valid_activity_codes": valid_activity_codes
        }
    )

VALID_ACTIVITY_CODES = None





def extract_ontology_distribution(results):

    labels = [
        ("Mechanistic / Basic Science", "mechanistic"),
        ("Therapeutic", "therapeutic"),
        ("Diagnostic", "diagnostic"),
        ("Research Tool", "research_tool"),
        ("Clinical / Health Systems", "clinical"),
        ("Research Infrastructure", "infrastructure"),
        ("Education / Training", "education"),
        ("Observational Epidemiology", "obs_ep")
    ]

    totals = {}

    for display_name, key in labels:

        total = 0

        for r in results["records"]:

            if r.get(key)==1:

                total += r.get("amount") or 0

        totals[display_name] = total

    ontology_labels = list(totals.keys())

    ontology_values = list(totals.values())

    

    return ontology_labels, ontology_values


@app.get("/search")

def search(request: Request,
    query: str = Query(..., description="Search query string")):

    
    # warm up models to reduce initial latency
    warmup_query_encoder()
    
    
    #normalize query before searching
    query = normalize_query(query)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if cached_results := get_cached_results(cur, query):
            years, funding = extract_funding(cached_results)
            ontology_labels, ontology_values = extract_ontology_distribution(cached_results)
            print(cached_results["records"][0].keys())


            return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "query": query,
                "years": years,
                "funding": funding,
                "results": cached_results["records"],
                "ontology_labels": ontology_labels,
                "ontology_values": ontology_values
            }
    )
    
        #prepare HNSW search parameters
        cur.execute("SET hnsw.ef_search = 1000;")
     
        #perform semantic search
        results = semantic_search_range(query, cur, rerank_fn=rerank_fn)

        #cache results
        save_cached_results(cur, query, results)
        conn.commit()
        
        years, funding = extract_funding(results)

        ontology_labels, ontology_values = extract_ontology_distribution(results)

        print(results["records"][0].keys())

        return templates.TemplateResponse(
            "results.html",
           {
            "request": request,
            "query": query,
            "years": years,
            "funding": funding,
            "results": results["records"],
            "ontology_labels": ontology_labels,
            "ontology_values": ontology_values
            }
    )
    finally:
        conn.close()

@ app.route("/portfolio")

def portfolio_page(request: Request):

    return templates.TemplateResponse(
        "portfolio.html",
        {"request": request}
    )

@ app.route("/categories")

def categories_page(request: Request):

    return templates.TemplateResponse(
        "categories.html",
        {"request": request}
    )

@app.get("/agency/{agency_code}", response_class=HTMLResponse)
def agency_portal(request: Request, agency_code: str):
    t0 = time.time()
    conn = get_db_connection()
    cur = conn.cursor()

    try: 
       
        target_code = agency_code.upper()

        # ====================================================================
        # 📈 STEP 1: HISTORICAL DATA FOR CHARTS (Blazing Fast DB Aggregations)
        # ====================================================================
        t_start = time.time()
        # A. Fetch historical timeline totals (1985-2026)
        timeline_query = """
            SELECT fiscal_year, SUM(total_award_amount)
            FROM ResearchGrants
            WHERE agency_code = %s
            GROUP BY fiscal_year
            ORDER BY fiscal_year ASC;
        """
        cur.execute(timeline_query, (target_code,))
        timeline_rows = cur.fetchall()
        print(f"⏱️ DB Timeline Query took: {time.time() - t_start:.4f}s")
        years = [row[0] for row in timeline_rows]
        funding = [float(row[1]) if row[1] else 0.0 for row in timeline_rows]

        # B. Fetch macro ontology distribution totals across all history
        t_start = time.time()
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
        print(f"⏱️ DB Ontology Query took: {time.time() - t_start:.4f}s")
        ontology_labels = [
            "Mechanistic / Basic Science", "Therapeutic", "Diagnostic", "Research Tool", 
            "Clinical / Health Systems", "Research Infrastructure", "Education / Training", "Observational Epidemiology"
        ]
        ontology_values = [float(val) for val in onto_row] if onto_row else [0.0] * 8


        # ====================================================================
        # 📋 STEP 2: TABLE REVIEWS (Filtered Strictly to 2025 Viewport)
        # ====================================================================
        t_start = time.time()
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

        cur.close()
        conn.close()

        # ====================================================================
        # 🏢 STEP 3: RESOLVE CSV METADATA DISPLAY NAME
        # ====================================================================
        t_start = time.time()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.abspath(os.path.join(script_dir, "..", "core", "agency", "agencies_updated.csv"))
        
        display_title = f"Agency Portfolio: {target_code}"
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            matched_rows = df[df["funding_code"] == target_code]["agency_ic"].values
            if len(matched_rows) > 0:
                display_title = matched_rows[0]
        print(f"⏱️ CSV Metadata Parsing took: {time.time() - t_start:.4f}s")
        # ====================================================================
        # 🎨 STEP 4: RENDER RESULTS PAGE INSTANTLY
        # ====================================================================
        print(f"🚀 TOTAL BACKEND RUNTIME: {time.time() - t0:.4f}s")
        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "query": display_title,
                "years": years,
                "funding": funding,
                "results": grants, # Populates the 2025 UI data table view flawlessly
                "ontology_labels": ontology_labels,
                "ontology_values": ontology_values
            }
        )
        
    except Exception as e:
        print(f"❌ Error generating metric analytics layer inside agency route: {e}")
        raise HTTPException(status_code=500, detail="Internal server metric analytics error.")
    finally:
        conn.close()

@app.get("/activity_codes", response_class=HTMLResponse)
def activity_codes_multi_search(
    request: Request, 
    codes: str = Query(..., description="Comma-separated 3-character NIH Activity codes")
):
    t0 = time.time()
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 1. Parse and sanitize input (Extracts exactly what the user typed)
        target_codes = [c.strip().upper() for c in codes.split(",") if c.strip()]
        if not target_codes or len(target_codes) > 5:
            raise HTTPException(status_code=400, detail="Must provide between 1 and 5 activity codes.")
            
        tuple_codes = tuple(target_codes)

        # ====================================================================
        # 📈 STEP 1: HISTORICAL DATA FOR CHARTS
        # ====================================================================
        t_start = time.time()
        # Strictly check against the 3-character activity code substring
        timeline_query = """
            SELECT fiscal_year, SUM(total_award_amount)
            FROM ResearchGrants
            WHERE activity_code IN %s
            GROUP BY fiscal_year
            ORDER BY fiscal_year ASC;
        """
        # Exactly 1 placeholder requires exactly 1 tuple wrapper
        cur.execute(timeline_query, (tuple_codes,))
        timeline_rows = cur.fetchall()
        print(f"⏱️ DB Timeline Query took: {time.time() - t_start:.4f}s")
        
        years = [row[0] for row in timeline_rows]
        funding = [float(row[1]) if row[1] else 0.0 for row in timeline_rows]

        # Fetch category distribution totals strictly via substring matching
        t_start = time.time()
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
            WHERE rg.activity_code IN %s;
        """
        # Exactly 1 placeholder here as well
        cur.execute(ontology_query, (tuple_codes,))
        onto_row = cur.fetchone()
        print(f"⏱️ DB Ontology Query took: {time.time() - t_start:.4f}s")
        
        ontology_labels = [
            "Mechanistic / Basic Science", "Therapeutic", "Diagnostic", "Research Tool", 
            "Clinical / Health Systems", "Research Infrastructure", "Education / Training", "Observational Epidemiology"
        ]
        ontology_values = [float(val) for val in onto_row] if onto_row else [0.0] * 8

        # ====================================================================
        # 📋 STEP 2: TABLE REVIEWS (2025 Viewport Only)
        # ====================================================================
        t_start = time.time()
        table_query = """
            SELECT
                rg.grant_id,
                rg.project_title,
                o.name AS organization,
                rg.contact_pi_id,
                rg.total_award_amount,
                rg.agency_ic,
                rg.fiscal_year,
                gl.mechanistic, gl.therapeutic, gl.diagnostic, gl.research_tool,
                gl.clinical, gl.infrastructure, gl.education, gl.obs_ep,               
                s.two_sentence_summary AS summary_text
            FROM ResearchGrants rg
            JOIN grant_labels gl ON rg.grant_id = gl.grant_id
            INNER JOIN Grant_Summaries s ON rg.grant_id = s.grant_id
            LEFT JOIN organizations o ON rg.organization_id = o.id
            WHERE 
                rg.activity_code IN %s
                AND rg.fiscal_year = 2025
            ORDER BY rg.total_award_amount DESC;
        """
        # Exactly 1 placeholder maps cleanly to the target tuple wrapper
        cur.execute(table_query, (tuple_codes,))
        rows = cur.fetchall()
        print(f"⏱️ DB 2025 Table Query took: {time.time() - t_start:.4f}s")
        
        grants = []
        for row in rows:
            grant_id = row[0]
            activity_code = grant_id[1:4] if len(grant_id) > 4 else "N/A"

            grants.append({
                "grant_id": grant_id, "title": row[1], "organization": row[2] if row[2] else "Unknown Institution",
                "pi": row[3], "amount": float(row[4]) if row[4] else 0.0, "agency_ic": row[5], "fiscal_year": int(row[6]) if row[6] else 2025,                
                "mechanistic": row[7], "therapeutic": row[8], "diagnostic": row[9], "research_tool": row[10],
                "clinical": row[11], "infrastructure": row[12], "education": row[13], "obs_ep": row[14], "summary": row[15], "activity_code": activity_code
            })

        cur.close()
        conn.close()

        display_title = f"Activity Codes: {', '.join(target_codes)}"
        print(f"🚀 TOTAL BACKEND RUNTIME: {time.time() - t0:.4f}s")
        
        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "query": display_title,
                "years": years,
                "funding": funding,
                "results": grants,
                "ontology_labels": ontology_labels,
                "ontology_values": ontology_values
            }
        )
        
    except Exception as e:
        print(f"❌ Error in activity_codes route: {e}")
        if 'conn' in locals() and not conn.closed:
            conn.close()
        raise HTTPException(status_code=500, detail="Database lookup error.")


@app.get("/api/portfolio/categories")
def portfolio_categories(
    year: int,
    request: Request
):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
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

        """, (year,))

        row = cur.fetchone()

        output = {
            "Mechanistic / Basic Science": row[0] or 0,
            "Therapeutic": row[1] or 0,
            "Diagnostic": row[2] or 0,
            "Research Tool": row[3] or 0,
            "Clinical / Health Systems": row[4] or 0,
            "Research Infrastructure": row[5] or 0,
            "Education / Training": row[6] or 0,
            "Observational Epidemiology": row[7] or 0
        }

        return output

    finally:
        conn.close()

@app.get("/api/portfolio/grants")
def portfolio_grants(
    year: int,
    category: str,
    request: Request
):

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
        return {"error": "Invalid category"}

    column = category_columns[category]

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

        return {
            "category": category,
            "year": year,
            "grants": grants
        }

    finally:
        conn.close()


class SearchRequest(BaseModel):
    year: str
    category: Optional[str] = None
    query: str
    existing_ids: List[str] # Validated as a native array of strings
    query_history_count: int = 1  # use this to track queries to then route to either semantic or hybrid search
 


@app.post("/api/portfolio/grants/search")
def portfolio_grants_search(
    payload: SearchRequest
):

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

    # handle category verification if it is not provided
    column = None
    if payload.category:
        if payload.category not in category_columns:
            return {"error": "Invalid category"}
        column = category_columns[payload.category]

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # determine pool of grants to search

        # start with if frontend provides list of grants, use those

        if payload.existing_ids:
           allowed_grant_ids = [str(x).strip() for x in payload.existing_ids if x]

        # if not, filter by category but not by existing list
        else: 
            if column: 
                # year and category filter
                sql = f"""

                    SELECT rg.grant_id

                    FROM ResearchGrants rg

                    JOIN grant_labels gl
                        ON rg.grant_id = gl.grant_id

                    WHERE
                        rg.fiscal_year = %s
                        AND gl.{column} = 1

                    """

                cur.execute(sql, (int(payload.year),))

            else: 
                # year filter only, no category, no existing list
                sql = """

                    SELECT grant_id
                    FROM ResearchGrants
                    WHERE fiscal_year = %s

                """

                cur.execute(sql, (int(payload.year),))

            allowed_grant_ids = [row[0] for row in cur.fetchall()]

        # ====================================================================
        # 🎛️ DYNAMIC SEARCH ROUTER MATRIX
        # ====================================================================
        # Determine if this request qualifies for Hybrid Substring Overrides:
        # Condition A: It's the 2nd or beyond sub-search for Options 1-3 (existing_ids present AND history > 1)
        # Condition B: It's a sub-search refining Option 4 (Global search page sub-filtering)
        is_nested_subsearch = payload.query_history_count > 1

        if is_nested_subsearch and allowed_grant_ids:
            print("🔍 Routing to HYBRID SEARCH (Semantic + Substring Filter)")
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

            scores = rerank_fn.remote(payload.query, [d["text"] for d in docs])
            ranked = combine_and_sort_semantic_filter(docs, scores)
            return {
                "query": payload.query,
                "category": payload.category,
                "year": payload.year,
                "grants": format_output_grants(ranked)
            }


        query_vec = embed_query(payload.query)
        query_vec_list = query_vec.tolist()

        candidates = retrieve_candidates_range_portfolio(
            cur,
            query_vec_list = query_vec_list,
            similarity_threshold = 0.25,
            allowed_grant_ids = allowed_grant_ids,
        )

        vector_sim_map = {gid: sim for gid, sim in candidates}

        grant_ids = list(vector_sim_map.keys())

        docs = load_grant_texts(cur, grant_ids)

        for d in docs:
            d["vector_similarity"] = vector_sim_map.get(d["grant_id"], 0.0)


        # reranking
        doc_texts = [d["text"] for d in docs]
        scores = rerank_fn.remote(payload.query, doc_texts)

        ranked = combine_and_sort_semantic_filter(docs, scores)


        return {
            "query": payload.query,
            "category": payload.category,
            "year": payload.year,
            "grants": format_output_grants(ranked)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search pipeline execution failed: {str(e)}")

    finally:
        conn.close()

def format_output_grants(ranked_docs):
    """Helper layout to normalize object fields perfectly for JavaScript render tracks"""
    for g in ranked_docs:
        g["organization"] = g.get("org_name")
        g["funding"] = g.get("amount")
        first, middle, last = g.get("pi_first_name") or "", g.get("pi_middle_name") or "", g.get("pi_last_name") or ""
        g["pi"] = " ".join(x for x in [first, middle, last] if x)
    return ranked_docs


@app.get("/api/grant/{grant_id}/abstract")
def get_grant_abstract(grant_id: str):
    
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT abstract
            FROM ResearchGrants
            WHERE grant_id = %s
        """, (grant_id,))

        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Grant not found.")
            
        return {"abstract": row[0] if row[0] else "No abstract available for this record."}

    finally:
        cur.close()
        conn.close()

@ app.route("/contact_us")

def contact_page(request: Request):

    return templates.TemplateResponse(
        "contact_us.html",
        {"request": request}
    )