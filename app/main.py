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

    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "agencies": agencies_list
        }
    )

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
                gl.obs_ep
            FROM ResearchGrants rg
            JOIN grant_labels gl ON rg.grant_id = gl.grant_id
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
                "obs_ep": row[14]
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
                rg.total_award_amount

            FROM ResearchGrants rg

            JOIN grant_labels gl
                ON rg.grant_id = gl.grant_id

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
                "funding": row[4]
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

        for g in ranked:

            g["organization"] = g.get("org_name")

            g["funding"] = g.get("amount")

            first = g.get("pi_first_name") or ""
            middle = g.get("pi_middle_name") or ""
            last = g.get("pi_last_name") or ""

            g["pi"] = " ".join(
                x for x in [first, middle, last] if x
            )

        return {
            "query": payload.query,
            "category": payload.category,
            "year": payload.year,
            "grants": ranked
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search pipeline execution failed: {str(e)}")

    finally:
        conn.close()

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

class FilterPayload(BaseModel):
    category: Optional[str] = None
    agency: Optional[str] = None

class DimensionPayload(BaseModel):
    # Basic Science / Default Lenses
    topic: bool = False
    project_type: bool = False
    agency: bool = False
    geography: bool = False
    career_stage: bool = False
    
    # Education / Training Lenses
    institutional_equity: bool = False
    geographic_diversity: bool = False
    pipeline_transition: bool = False
    
    # Therapeutics & Clinical Lenses
    translational_velocity: bool = False
    commercial_pipeline: bool = False

class PortfolioBriefingRequest(BaseModel):
    grant_ids: List[str] = Field(..., description="List of active filtered grant IDs")
    search_queries: List[str] = Field(default_factory=list)
    filters: FilterPayload
    dimensions: DimensionPayload



LENS_REGISTRY = {
    "institutional_equity": InstitutionalEquityStrategy(),
}


@app.post("/api/summarize-portfolio")
async def generate_portfolio_briefing(payload: PortfolioBriefingRequest):
    category = payload.filters.category  # e.g., "education", "mechanistic", or None
    grant_ids = payload.grant_ids
    queries = payload.search_queries

    # 1. Identify which lens dimension was flagged as True
    # .model_dump() turns the Pydantic sub-object into a standard dict
    dimension_dict = payload.dimensions.model_dump()
    active_dimension = next((dim for dim, active in dimension_dict.items() if active), "topic")

    strategy = LENS_REGISTRY.get(active_dimension)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        ids = [str(x) for x in payload.grant_ids if x]

        active_grants = strategy.load_grant_details(cur, ids)

        if not active_grants:
            raise HTTPException(status_code=400, detail="No grants found for the provided IDs.")

        t_cluster_start = time.perf_counter()
        script_dir = os.path.dirname(os.path.abspath(__file__))

        clusters = strategy.partition_workspace(active_grants, script_dir)
        t_cluster_end = time.perf_counter()
        print(f"⏱️ [LATENCY] Clustering Step: {t_cluster_end - t_cluster_start:.4f} seconds")

        total_filtered_budget = sum(float(g.get("amount") or 0) for g in active_grants)


        query_intersection = "N/A"
        
        query_intersection = "N/A"
        clean_queries = [q.strip() for q in payload.search_queries if q.strip()]
        if clean_queries:
            query_intersection = " AND ".join([f"'{q}'" for q in clean_queries])

        category_human_name = "N/A"
        if payload.filters.category:
            category_human_name = machine_human_map.get(payload.filters.category, payload.filters.category)

        agency_human_name = "N/A"
        if payload.filters.agency:
            csv_path = os.path.abspath(os.path.join(script_dir, "..", "core", "agency", "agencies_updated.csv"))
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                matched = df[df["funding_code"] == str(payload.filters.agency)]["agency_ic"].values
                if len(matched) > 0:
                    agency_human_name = matched[0]

        # Build clean structural instructions for the Map LLM
        global_filters_context = f"- Active Search Queries: {query_intersection}\n"
        global_filters_context += f"- Active Agency Scope: {agency_human_name}\n"
        if payload.filters.category and category_human_name in category_mapping:
            global_filters_context += f"- Active Category Frame: {category_human_name} (Focus Area: {category_mapping[category_human_name]})\n"
        else:
            global_filters_context += f"- Active Category Frame: Broad/Unfiltered Dataset View\n"

        # Ask the strategy what its high-level description is
        active_lens_desc = getattr(strategy, "lens_description", "Custom Research Cohort")

        # ==========================================
        # 3. DISPATCH PARALLEL ASYNC MAP WORKERS
        # ==========================================
        t_map_start = time.perf_counter()

        async def process_cluster_chunk(cluster_id, items):
            t_chunk_start = time.perf_counter()
            
            cluster_budget = sum(float(g.get("amount") or 0) for g in items)
            budget_share_pct = (cluster_budget / total_filtered_budget * 100) if total_filtered_budget > 0 else 0
            short_cluster_budget = format_currency_short(cluster_budget)

            VISIBILITY_CEILING = 75
            context_lines = []

            for g in items[:VISIBILITY_CEILING]:
                title = g.get("title", "No Title")
                activity_code = g.get("grant_id", "")[1:4].upper() if g.get("grant_id") and len(g.get("grant_id")) >= 4 else "Other"
                amount = float(g.get("amount") or 0)
                formatted_amount = format_currency_short(amount)
                nano_summary = g.get("summary_text", "No summary available.")

                context_lines.append(
                    f"* [{activity_code} - {formatted_amount}] {title}\n"
                    f"  Scientific Core: {nano_summary}"
                )

            cluster_context = "\n".join(context_lines)

            # 🔑 DYNAMIC LAYOUT: Allow the strategy to define a custom map prompt if it wants one
            if hasattr(strategy, "build_map_prompt"):
                map_prompt = strategy.build_map_prompt(
                    cluster_id=cluster_id,
                    cluster_context=cluster_context,
                    short_cluster_budget=short_cluster_budget,
                    budget_share_pct=budget_share_pct,
                    global_filters_context=global_filters_context
                )
            else:
                # Fallback to your original baseline map prompt template
                map_prompt = f"""
                You are a technical program mapping assistant. Your job is to generate high-density, concise micro-summaries of specific grant buckets.
                CONTEXTUAL FILTER BOUNDARIES FOR THIS ANALYTICAL RUN:
                {global_filters_context}
                CURRENT COHORT PERSPECTIVE:
                - This cohort represents a discrete partition split by: {active_lens_desc}.
                - Active Target Partition Key Name: **{cluster_id}**
                - ACTIVE GRANTS LIST ASSIGNED TO THIS TARGET SECTOR (Showing up to {VISIBILITY_CEILING} high-density records):
                {cluster_context}
                CRITICAL FINANCIAL METRICS FOR THIS SECTOR:
                - Allocated Total Capital: ${short_cluster_budget} 
                - Workspace Share Density: {budget_share_pct:.1f}% of total active filtered portfolio view.
                Provide a highly objective, technical, 2-sentence summary outlining the unified scientific objectives or operational focus of this group.
                CRITICAL DESIGN RULE: You MUST open your response exactly matching this explicit formatting rule:
                "Accounting for ${short_cluster_budget} ({budget_share_pct:.1f}% of the active portfolio budget), this cluster focuses on..."
                """

            response = await client.aio.models.generate_content(
                model="gemini-3-flash-preview", 
                contents=map_prompt
            )
            
            t_chunk_end = time.perf_counter()
            print(f"   ↳ [ASYNC MAP CHUNK] Resolved cluster '{cluster_id}' ({len(items)} grants): {t_chunk_end - t_chunk_start:.4f} seconds")
            
            return f"### Partition: {cluster_id}\n{response.text}"

        # 4. Dispatch tasks concurrently
        tasks = [process_cluster_chunk(cid, items) for cid, items in clusters.items()]
        cluster_summaries = await asyncio.gather(*tasks)

        t_map_end = time.perf_counter()
        print(f"⏱️ [LATENCY] Global Map Phase Total: {t_map_end - t_map_start:.4f} seconds")

        # ==========================================
        # 4. REDUCE PHASE (FINAL BRIEFING SYNTHESIS)
        # ==========================================
        t_reduce_start = time.perf_counter()
        master_context = "\n\n".join(cluster_summaries)
        short_total_budget = format_currency_short(total_filtered_budget)

        # Assemble your dictionary of parameters for the final reduce layout
        reduce_ctx = {
            "category_human_name": category_human_name,
            "short_total_budget": short_total_budget,
            "master_context": master_context
        }

        # Let the strategy render its custom target prompt template!
        final_reduce_prompt = strategy.build_reduce_prompt(reduce_ctx)

        final_briefing = await client.aio.models.generate_content(model = "gemini-3-flash-preview", contents = final_reduce_prompt)
        t_reduce_end = time.perf_counter()
        print(f"⏱️ [LATENCY] Reduce Phase Total (Final synthesis): {t_reduce_end - t_reduce_start:.4f} seconds")

        return {"summary": final_briefing.text}           
     
    finally:
        conn.close()
'''

@app.post("/api/summarize-portfolio")
async def summarize(
    payload: SummaryRequest
):
    t_start = time.perf_counter()

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # first we will generate a list of grant_ids to summarize based on the input string of comma-separated ids from the frontend

        t_db_start = time.perf_counter()

        # identify selected filter for analysis
        if payload.dimensions.agency: 
            active_lens = "agency"
        elif payload.dimensions.project_type:
            active_lens = "project_type"
        elif payload.dimensions.category:
            active_lens = "category"
        elif payload.dimensions.topic:
            active_lens = "topic"
        elif payload.dimensions.geography:
            active_lens = "geography"
        elif payload.dimensions.career_stage:
            active_lens = "career_stage"
        else:
            active_lens = "none"
        

        ids = [str(x) for x in payload.grant_ids if x]

        active_grants = load_grant_embeddings_and_text(cur, ids, active_lens=active_lens)

        if len(active_grants) > 0:
            sample_grant = active_grants[0]
            print("📊 [DATABASE PAYLOAD CHECK]")
            print(f"-> Available Dictionary Keys: {list(sample_grant.keys())}")
            print(f"-> Sample 'career_stage' value: {sample_grant.get('career_stage')}")
            
            # Count how many rows actually have a valid career stage string
            valid_stages = [g.get('career_stage') for g in active_grants if g.get('career_stage') and g.get('career_stage') != 'Unclassified']
            print(f"-> Total grants with active career classifications: {len(valid_stages)} / {len(active_grants)}")

        if not active_grants:
            raise HTTPException(status_code=400, detail="No grants found.") 

        t_db_end = time.perf_counter()
        print(f"⏱️ [LATENCY] DB Ingestion ({len(active_grants)} grants): {t_db_end - t_db_start:.4f} seconds")

        t_cluster_start = time.perf_counter()

        # calculate total budget
        total_filtered_budget = sum(float(g.get("amount") or 0) for g in active_grants)

               


        # Route to different clustering strategies based on the selected lens
        clusters: Dict[str, List[dict]] = {}
        script_dir = os.path.dirname(os.path.abspath(__file__))

        if active_lens == "agency":
            # Load agency lookup map ONCE outside the loops to optimize memory I/O
            agency_lookup = {}
            csv_path = os.path.abspath(os.path.join(script_dir, "..", "core", "agency", "agencies_updated.csv"))
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                agency_lookup = dict(zip(df["funding_code"].astype(str), df["agency_ic"]))

            for g in active_grants:
                raw_code = g.get("agency_code")
                key = str(raw_code or "Unknown Agency")
                
                # Check if it exists in your lookup map
                if key in agency_lookup:
                    full_name = agency_lookup[key]
                else:
                    full_name = f"Unmapped Agency (Code: {key})"
                    # 🚨 LOUD LOGGING INTERVENTION: Catch the culprit!
                    print(f"⚠️ SERVER WARNING: Found unmapped funding code '{raw_code}' for Grant ID {g.get('grant_id')} (Amount: ${g.get('amount')})")
                
                clusters.setdefault(full_name, []).append(g)
        
        elif active_lens == "project_type":
            for g in active_grants:
                # Fallback safely if grant_id layout changes or is missing
                gid = g.get("grant_id", "")
                activity_code = gid[1:4].upper() if len(gid) >= 4 else "Other"
                clusters.setdefault(activity_code, []).append(g)
        
        elif active_lens == "category":
            intent_keys = ["mechanistic", "therapeutic", "diagnostic", "clinical", "research_tool", "infrastructure", "education", "obs_ep"]
            for g in active_grants:
                # 1. First pass: Find all matching categories for this specific grant
                matched_keys = []
                for k in intent_keys:
                    if g.get(k) == 1 or g.get(k) == "1" or g.get(k) is True:
                        matched_keys.append(k)
                
                # 2. Second pass: Calculate fractional weight and distribute to clusters
                if matched_keys:
                    match_count = len(matched_keys)
                    
                    # Safely parse the original grant budget amount
                    original_amount = float(g.get("amount") or 0)
                    
                    # Split the amount evenly across all matched categories
                    fractional_amount = original_amount / match_count
                    
                    for k in matched_keys:
                        human_label = machine_human_map.get(k, k.replace("_", " ").title())
                        
                        # Create a shallow copy of the grant dict so we don't mutate 
                        # the shared reference for other categories or downstream loops
                        fractional_grant = g.copy()
                        fractional_grant["amount"] = fractional_amount
                        
                        clusters.setdefault(human_label, []).append(fractional_grant)
                else:
                    # Handle grants that carry zero intent flags
                    clusters.setdefault("Uncategorized Intent", []).append(g)

        elif active_lens == "topic":
            clusters = cluster_filtered_grants_for_map(active_grants)

        elif active_lens == "geography":
            for g in active_grants:
                org_state = g.get("org_state", "Unknown State")
                clusters.setdefault(org_state, []).append(g)

        elif active_lens == "career_stage":
            for g in active_grants:
                stage = g.get("career_stage", "Unclassified")
                clusters.setdefault(stage, []).append(g)

        t_cluster_end = time.perf_counter()
        print(f"⏱️ [LATENCY] Sorting/Clustering ({len(clusters)} buckets via '{active_lens}'): {t_cluster_end - t_cluster_start:.4f} seconds")

        # --- CONSTRUCT RESILIENT SEARCH CONTEXT ---

        query_intersection = "N/A"
        clean_queries = [q.strip() for q in payload.search_queries if q.strip()]
        if clean_queries:
            query_intersection = " AND ".join([f"'{q}'" for q in clean_queries])

        category_human_name = "N/A"
        if payload.filters.category:
            category_human_name = machine_human_map.get(payload.filters.category, payload.filters.category)

        agency_human_name = "N/A"
        if payload.filters.agency:
            csv_path = os.path.abspath(os.path.join(script_dir, "..", "core", "agency", "agencies_updated.csv"))
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                matched = df[df["funding_code"] == str(payload.filters.agency)]["agency_ic"].values
                if len(matched) > 0:
                    agency_human_name = matched[0]

        # Build clean structural instructions for the Map LLM
        global_filters_context = f"- Active Search Queries: {query_intersection}\n"
        global_filters_context += f"- Active Agency Scope: {agency_human_name}\n"
        if payload.filters.category and category_human_name in category_mapping:
            global_filters_context += f"- Active Category Frame: {category_human_name} (Focus Area: {category_mapping[category_human_name]})\n"
        else:
            global_filters_context += f"- Active Category Frame: Broad/Unfiltered Dataset View\n"

        lens_descriptions = {
            "agency": "Administering NIH Institute/Center Classification",
            "project_type": "NIH Grant Activity Mechanism (e.g., R01, R21, U54)",
            "category": "Downstream Grant Intent Canvas Block",
            "topic": "Semantic Research Abstract Focus Cluster",
            "geography": "Geographic Distribution by State of Awardee Institution",
            "career_stage": "Principal Investigator Operational Longevity and Academic Vintage Cohort"
        }
        active_lens_desc = lens_descriptions.get(active_lens, "Custom Research Cohort")

        t_map_start = time.perf_counter()

        # 1. Define an async worker function to handle an isolated cluster payload
        async def process_cluster_chunk(cluster_id, items):
            t_chunk_start = time.perf_counter()
            
            # ======================================================================
            # 🚀 FOR TOPIC LENS: READ PRE-CALCULATED METRICS DIRECTLY
            # ======================================================================
            if active_lens == "topic":
                # Rename 'items' to 'cluster_payload' for semantic clarity
                cluster_payload = items 
                
                # Pull pre-calculated budget footprints out of the payload
                cluster_budget = float(cluster_payload.get("total_budget", 0))
                budget_share_pct = (cluster_budget / total_filtered_budget * 100) if total_filtered_budget > 0 else 0
                short_cluster_budget = format_currency_short(cluster_budget)
                
                # Read the pre-built search query string to use as a grounding phrase
                suggested_search = cluster_payload.get("generated_web_search_query", "")
                
                # Unpack the pre-sorted consensus core projects
                core_projects = cluster_payload.get("consensus_core", [])
                core_titles_str = "\n      ".join([
                    f"* Title: {p['title']} ({p.get('mechanism', 'R01')} - ${p['amount']/1e6:.1f}M)" 
                    for p in core_projects
                ])
                
                # Unpack the pre-filtered innovation outliers
                outliers = cluster_payload.get("high_innovation_outliers", [])
                if outliers:
                    outliers_str = "\n      ".join([
                        f"* Title: {p['title']} ({p.get('mechanism', 'R21')} - ${p['amount']/1e6:.1f}M) [Distance: {p.get('distance_score', 0):.3f}]"
                        for p in outliers
                    ])
                else:
                    outliers_str = "* None identified on the semantic periphery using agile vehicles."
                    
                # 🏢 GOOGLE GROUNDING CHANGE: We no longer execute a manual search api here.
                # We pass the instruction straight to the final high-capability model instead.

                # Construct the final rich briefing payload for the REDUCE phase
                chunk_payload = f"""
                    - Mathematically Derived Topic Cluster ID: {cluster_id}
                    - Total Aggregated Budget Footprint: ${short_cluster_budget}
                    - Total Project Count Volume: {cluster_payload.get('project_count', 0)} grants ({budget_share_pct:.1f}% of total workspace share)
                    - Core Consensus Projects (Cluster Center):
                        {core_titles_str}
                    - Structurally Protected High-Innovation Outliers (Semantic Boundary + Agile Mechanism):
                        {outliers_str}
                    - Suggested Grounding Search Phrase: "{suggested_search}"
                    """
                t_chunk_end = time.perf_counter()
                print(f"   ↳ [SPATIAL MAP CHUNK] Resolved topic cluster '{cluster_id}': {t_chunk_end - t_chunk_start:.4f} seconds")
                return chunk_payload

            # ======================================================================
            # 🏢 FOR ALL OTHER LENSES (AGENCY, ACTIVITY CODE): RUN ORIGINAL UNPACKING
            # ======================================================================
            else:
                # 'items' is guaranteed to be a list of raw grant dicts here
                cluster_budget = sum(float(g.get("amount") or 0) for g in items)
                budget_share_pct = (cluster_budget / total_filtered_budget * 100) if total_filtered_budget > 0 else 0
                short_cluster_budget = format_currency_short(cluster_budget)

                VISIBILITY_CEILING = 75
                context_lines = []

                for g in items[:VISIBILITY_CEILING]:
                    title = g.get("title", "No Title")
                    activity_code = g.get("grant_id", "")[1:4].upper() if g.get("grant_id") and len(g.get("grant_id")) >= 4 else "Other"
                    
                    amount = float(g.get("amount") or 0)
                    formatted_amount = format_currency_short(amount)

                    nano_summary = g.get("summary_text", "No summary available.")

                    context_lines.append(
                        f"* [{activity_code} - {formatted_amount}] {title}\n"
                        f"  Scientific Core: {nano_summary}"
                    )


                cluster_context = "\n".join(context_lines)

                map_prompt = f"""
                You are a technical program mapping assistant. Your job is to generate high-density, concise micro-summaries of specific grant buckets.
                CONTEXTUAL FILTER BOUNDARIES FOR THIS ANALYTICAL RUN:
                {global_filters_context}
                CURRENT COHORT PERSPECTIVE:
                - This cohort represents a discrete partition split by: {active_lens_desc}.
                - Active Target Partition Key Name: **{cluster_id}**
                - ACTIVE GRANTS LIST ASSIGNED TO THIS TARGET SECTOR (Showing up to {VISIBILITY_CEILING} high-density records):
                {cluster_context}
                CRITICAL FINANCIAL METRICS FOR THIS SECTOR:
                - Allocated Total Capital: ${short_cluster_budget} 
                - Workspace Share Density: {budget_share_pct:.1f}% of total active filtered portfolio view.
                Provide a highly objective, technical, 2-sentence summary outlining the unified scientific objectives or operational focus of this group.
                CRITICAL DESIGN RULE: You MUST open your response exactly matching this explicit formatting rule:
                "Accounting for ${short_cluster_budget} ({budget_share_pct:.1f}% of the active portfolio budget), this cluster focuses on..."
                """

                response = await client.aio.models.generate_content(
                    model="gemini-3-flash-preview", 
                    contents=map_prompt
                )
                
                t_chunk_end = time.perf_counter()
                print(f"   ↳ [ASYNC MAP CHUNK] Resolved cluster '{cluster_id}' ({len(items)} grants): {t_chunk_end - t_chunk_start:.4f} seconds")
                
                return f"### Institute Partition: {cluster_id}\n{response.text}"

        # 2. Build a task list of all coroutines to execute in parallel
        tasks = [
            process_cluster_chunk(cluster_id, items) 
            for cluster_id, items in clusters.items()
        ]

        # 3. Dispatch all tasks simultaneously and wait for the batch to resolve
        cluster_summaries = await asyncio.gather(*tasks)

        t_map_end = time.perf_counter()
        print(f"⏱️ [LATENCY] Global Map Phase Total (Concurrent Parallel Batch): {t_map_end - t_map_start:.4f} seconds")

        # create master briefing
        t_reduce_start = time.perf_counter()
        master_context = "\n\n".join(cluster_summaries)

        short_total_budget = format_currency_short(total_filtered_budget)
        
        # route to different reduce_prompts depending on selection
        if active_lens == "agency":
            missions_json_path = os.path.abspath(os.path.join(script_dir, "..", "core", "agency", "nih_missions.json"))
                        
            agency_missions_reference = "No official mission statements available for the active cohort."
            
            if os.path.exists(missions_json_path):
                with open(missions_json_path, "r") as f:
                    missions_db = json.load(f)
                    
                # Build a text block of ONLY the agencies present in the user's active results
                reference_lines = []
                for cluster_id in clusters.keys():
                    matching_data = lookup_mission_by_name(cluster_id, missions_db)
                    if matching_data:
                        reference_lines.append(f"- **{matching_data['full_name']}**: {matching_data['mission']}")
                
                if reference_lines:
                    agency_missions_reference = "\n".join(reference_lines)

            
            reduce_prompt = REDUCE_PROMPT_AGENCY.format(
                active_cat_name = category_human_name,
                query_intersection = query_intersection,
                total_filtered_budget = short_total_budget,
                master_context = master_context,
                agency_missions_reference = agency_missions_reference
            )        
            final_briefing = await client.aio.models.generate_content(model = "gemini-3-flash-preview", contents = reduce_prompt)
            t_reduce_end = time.perf_counter()
            print(f"⏱️ [LATENCY] Reduce Phase Total (Final synthesis): {t_reduce_end - t_reduce_start:.4f} seconds")

        elif active_lens == "project_type":
            code_mapping_csv = os.path.abspath(os.path.join(script_dir, "..", "core", "synthesis_prompts", "ActivityCodes.csv"))
            
            project_type_reference = "No official activity code definitions available for the active cohort."
            
            if os.path.exists(code_mapping_csv):
                df = pd.read_csv(code_mapping_csv)
                
                # 1. Build a rich lookup dictionary from the dataframe
                # Note the corrected column name: 'Activity_Code'
                code_lookup = {}
                for _, row in df.iterrows():
                    code = str(row["Activity_Code"]).strip()
                    code_lookup[code] = {
                        "title": row.get("Title", "Unknown Mechanism"),
                        "description": row.get("Description", "No description provided.")
                    }

                # 2. Extract and format ONLY the activity codes present in this active run
                reference_lines = []
                for cluster_id in clusters.keys():
                    # 💡 RESILIENCE TRICK: Extract the raw code prefix (e.g., turns "R01 - Research Project" into "R01")
                    clean_code_key = str(cluster_id).split()[0].split('-')[0].strip().upper()
                    
                    if clean_code_key in code_lookup:
                        meta = code_lookup[clean_code_key]
                        reference_lines.append(f"- **{clean_code_key} ({meta['title']})**: {meta['description']}")
                    else:
                        # Fallback case if cluster keys are already descriptive but missing from CSV
                        reference_lines.append(f"- **{cluster_id}**: Active project mechanism bucket.")

                if reference_lines:
                    project_type_reference = "\n".join(reference_lines)

            # 3. Format the final Reduce prompt with the new reference block parameter
            reduce_prompt = REDUCE_PROMPT_PROJECT_TYPE.format(
                active_cat_name = category_human_name,
                query_intersection = query_intersection,
                total_filtered_budget = short_total_budget,
                master_context = master_context,
                project_type_reference = project_type_reference  # Injecting the mechanism dictionary
            )
            final_briefing = await client.aio.models.generate_content(model = "gemini-3-flash-preview", contents = reduce_prompt)
            t_reduce_end = time.perf_counter()
            print(f"⏱️ [LATENCY] Reduce Phase Total (Final synthesis): {t_reduce_end - t_reduce_start:.4f} seconds")

        elif active_lens == "geography":
            reduce_prompt = REDUCE_PROMPT_GEOGRAPHY.format(
                active_cat_name = category_human_name,
                query_intersection = query_intersection,
                total_filtered_budget = short_total_budget,
                master_context = master_context
            )
            final_briefing = await client.aio.models.generate_content(model = "gemini-3-flash-preview", contents = reduce_prompt)
            t_reduce_end = time.perf_counter()
            print(f"⏱️ [LATENCY] Reduce Phase Total (Final synthesis): {t_reduce_end - t_reduce_start:.4f} seconds")
        
        elif active_lens == "career_stage":
            reduce_prompt = REDUCE_PROMPT_CAREER_STAGE.format(
                active_cat_name = category_human_name,
                query_intersection = query_intersection,
                total_filtered_budget = short_total_budget,
                master_context = master_context
            )
            final_briefing = await client.aio.models.generate_content(model = "gemini-3-flash-preview", contents = reduce_prompt)
            t_reduce_end = time.perf_counter()
            print(f"⏱️ [LATENCY] Reduce Phase Total (Final synthesis): {t_reduce_end - t_reduce_start:.4f} seconds")

        elif active_lens == "category":
            # 🚀 Cleanly stringify ONLY the definitions that are actually inside our active results
            reference_lines = []
            for cluster_id in clusters.keys():
                if cluster_id in category_mapping:
                    reference_lines.append(f"- **{cluster_id}**: {category_mapping[cluster_id]}")
                else:
                    reference_lines.append(f"- **{cluster_id}**: Supplementary uncategorized raw database partition.")
            
            category_definitions_reference = "\n".join(reference_lines)

            reduce_prompt = REDUCE_PROMPT_CATEGORY.format(
                active_cat_name = category_human_name,
                query_intersection = query_intersection,
                total_filtered_budget = short_total_budget,
                master_context = master_context,
                category_definitions_reference = category_definitions_reference
            )
            final_briefing = await client.aio.models.generate_content(model = "gemini-3-flash-preview", contents = reduce_prompt, config={"tools": [{"google_search": {}}]})
            t_reduce_end = time.perf_counter()
            print(f"⏱️ [LATENCY] Reduce Phase Total (Final synthesis): {t_reduce_end - t_reduce_start:.4f} seconds")

            
          
        elif active_lens == "topic":

            target_template = TOPIC_PROMPT_REGISTRY.get(category_human_name, DEFAULT_PROMPT_REDUCE_TOPIC)
            
            reduce_prompt = target_template.format(
                active_cat_name = category_human_name,  
                query_intersection = query_intersection,
                total_filtered_budget = short_total_budget,
                master_context = master_context
            )
            # use google grounding for topic lens, no additional reference needed
            final_briefing = await client.aio.models.generate_content(model = "gemini-3-flash-preview", contents = reduce_prompt, config={"tools": [{"google_search": {}}]})
            t_reduce_end = time.perf_counter()
            print(f"⏱️ [LATENCY] Reduce Phase Total (Final synthesis): {t_reduce_end - t_reduce_start:.4f} seconds")
            
       
        t_total_end = time.perf_counter()
        print(f"🏁 [LATENCY] TOTAL PIPELINE EXECUTION LIFETIME: {t_total_end - t_start:.4f} seconds\n")
        return {"summary": final_briefing.text}
            

     
    finally:
        conn.close()
'''
@ app.route("/contact_us")

def contact_page(request: Request):

    return templates.TemplateResponse(
        "contact_us.html",
        {"request": request}
    )