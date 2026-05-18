#main.py

from fastapi import FastAPI, Query, Request, HTTPException
from core.db.connection import get_db_connection
from core.search.search_service_prod import semantic_search_range
from core.search.cache import get_cached_results, save_cached_results
from core.search.query_embedding import warmup_query_encoder
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from datetime import datetime
from core.search.modal_reranker import rerank_fn
from core.search.combine import combine_and_sort
from core.search.query_embedding import embed_query
from core.search.candidate_retrieval import retrieve_candidates_range_portfolio
from core.search.load_docs import load_grant_texts
from core.cluster.agglomerative_clustering import cluster_filtered_grants
from core.cluster.load_embeddings_text import load_grant_embeddings_and_text
from google import genai
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os
from core.category.mapping import category_mapping, machine_human_map
import pandas as pd

load_dotenv()

client = genai.Client()

app = FastAPI(title="NIH Grant Search API")

app.mount("/static", StaticFiles(directory="./app/static"), name="static")
templates = Jinja2Templates(directory="./app/templates")

class SummaryRequest(BaseModel):
    grant_ids: List[str] # Looks for "grant_ids"
    active_category: str
    search_queries: List[str] 

class SearchRequest(BaseModel):
    year: str
    category: str
    query: str
    existing_ids: List[str] # Validated as a native array of strings


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
    conn = get_db_connection()
    cur = conn.cursor()

    try: 
        target_code = agency_code.upper()

        # 1. Update query to pull the exact timeline and ontology columns your analytical blocks need
        query = """
            
            SELECT
                rg.grant_id,
                rg.project_title,
                o.name AS organization,
                rg.contact_pi_id,
                rg.total_award_amount,  -- Maps to 'amount' below
                rg.abstract,
                rg.agency_ic,
                rg.fiscal_year,         -- Crucial for extract_funding()
                gl.mechanistic,         -- Crucial for extract_ontology_distribution()
                gl.therapeutic,
                gl.diagnostic,
                gl.research_tool,
                gl.clinical,
                gl.infrastructure,
                gl.education,
                gl.obs_ep
            FROM ResearchGrants rg
            LEFT JOIN grant_labels gl
                ON rg.grant_id = gl.grant_id
            LEFT JOIN organizations o
                ON rg.organization_id = o.id
            WHERE
                rg.agency_code = %s
            ORDER BY rg.fiscal_year ASC, rg.total_award_amount DESC
        """

        cur.execute(query, (target_code,))
        rows = cur.fetchall()

        grants = []
        for row in rows:
            grants.append({
                "grant_id": row[0],
                "title": row[1],
                "organization": row[2] if row[2] else "Unknown Institution",
                "pi": row[3],
                "amount": float(row[4]) if row[4] else 0.0,  # ✨ Named 'amount' to feed extract functions!
                "abstract": row[5] if row[5] else "",
                "agency_ic": row[6],
                "fiscal_year": int(row[7]) if row[7] else datetime.now().year, # ✨ Fed to extract_funding
                
                # ✨ Ontology keys matching your exact mapping structure lookups
                "mechanistic": row[8],
                "therapeutic": row[9],
                "diagnostic": row[10],
                "research_tool": row[11],
                "clinical": row[12],
                "infrastructure": row[13],
                "education": row[14],
                "obs_ep": row[15]
            })

        # 2. Package into the structure your helper systems expect
        envelope = {"records": grants}

        # 3. Leverage your existing core functional workflows instantly! 🚀
        years, funding = extract_funding(envelope)
        ontology_labels, ontology_values = extract_ontology_distribution(envelope)

        # 4. Resolve the Human Readable Display Name from your localized asset mapping
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.abspath(os.path.join(script_dir, "..", "core", "agency", "agencies_updated.csv"))
        
        display_title = f"Agency Portfolio: {target_code}"
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            matched_rows = df[df["funding_code"] == target_code]["agency_ic"].values
            if len(matched_rows) > 0:
                display_title = matched_rows[0]


        # 5. Hand over data to results.html dashboard canvas tracking variables
        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "query": display_title,
                "years": years,
                "funding": funding,
                "results": grants, # Keep passing the raw parsed list to your frontend cards table loop
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
                rg.total_award_amount,
                rg.abstract

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
                "funding": row[4],
                "abstract": row[5]
            })

        return {
            "category": category,
            "year": year,
            "grants": grants
        }

    finally:
        conn.close()

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
            
            sql = f"""

                SELECT rg.grant_id

                FROM ResearchGrants rg

                JOIN grant_labels gl
                    ON rg.grant_id = gl.grant_id

                WHERE
                    rg.fiscal_year = %s
                    AND gl.{column} = 1

                """

            cur.execute(sql, (year,))

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

        ranked = combine_and_sort(docs, scores)

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


@app.post("/api/summarize-portfolio")
def summarize(
    payload: SummaryRequest
):

    conn = get_db_connection()
    cur = conn.cursor()

    try:

        # first we will generate a list of grant_ids to summarize based on the input string of comma-separated ids from the frontend

        ids = [str(x) for x in payload.grant_ids if x]

        active_grants = load_grant_embeddings_and_text(cur, ids)

        if not active_grants:
            raise HTTPException(status_code=400, detail="No grants found.") 

        # calculate total budget
        total_filtered_budget = sum(float(g.get("amount") or 0) for g in active_grants)
        
        # run clustering on the active grants to group them into homogeneous fractions for better summarization by the LLM
  

        clusters = cluster_filtered_grants(active_grants)

        # summarize clusters concurrently 

        # --- CONSTRUCT INTERSECTIONAL SEARCH CONTEXT ---
        category_human_name = machine_human_map.get(payload.active_category, payload.active_category) 

    

        query_intersection = "No filters applied"

        # Filter out empty strings or whitespaces from the query list
        clean_queries = [q.strip() for q in payload.search_queries if q.strip()]
        
        if clean_queries:
            # e.g., ["CRISPR", "Oncology"] -> "CRISPR AND Oncology"
            query_intersection = " AND ".join([f"'{q}'" for q in clean_queries])

        cluster_summaries = []

        print("filters", query_intersection)
        for cluster_id, items in clusters.items():
            cluster_budget = sum(float(g.get("amount") or 0) for g in items)

            budget_share_pct = (cluster_budget / total_filtered_budget * 100) if total_filtered_budget > 0 else 0

            cluster_context = "\n".join([f"- Title: {g['title']}" for g in items[:15]])

            map_prompt = f"""
            You are analyzing a specialized cohort of research grants.
            These are grants that are categorized with intent of {category_human_name} and therefore are focused on {category_mapping[category_human_name]}.
            These grants also may or may not also be filtered by the following terms: {query_intersection}.

            
            Review this highly concentrated, semantically linked group of research grants and their funding:
            {cluster_context}
            
            CRITICAL FINANCIAL METRICS FOR THIS CLUSTER:
            - Total Allocated Funds: ${cluster_budget:,.2f}
            - Portfolio Budget Share: {budget_share_pct:.1f}% of the currently filtered view space.

            Provide a highly technical, 2-sentence summary of this cluster's scientific objective. 
            You MUST open the summary by explicitly stating its financial footprint, formatted exactly like this:
            "Accounting for ${cluster_budget:,.2f} ({budget_share_pct:.1f}% of the active portfolio budget), this cluster focuses on..."
            """
            response = client.models.generate_content(model = "gemini-3-flash-preview", contents = map_prompt)
            cluster_summaries.append(response.text)

        # create master briefing
        master_context = "\n\n".join(cluster_summaries)
        reduce_prompt = f"""
        You are a principal scientific program director. You are analyzing research grants that are categorized with intent of {category_human_name} and therefore are focused on {category_mapping[category_human_name]}.
        These grants also may or may not also be filtered by the following terms: {query_intersection}.
        
        The total budget of the relevant space is: ${total_filtered_budget:,.2f}.

        Below are thematic summaries describing distinct clusters of grants within the above category and filters:
        
        {master_context}
        
        Synthesize these into an executive-level dossier. You must adhere to the following strict layout and formatting rules:
        1. DO NOT use generic bolded bullet points like '** Cluster Name **' or '* **Focus:**'. Use clean, professional paragraph prose under standard markdown headers.
        2. Every cluster mentioned must be contextualized by the dollar amount ($) or budget percentage (%) allocated to it.
        3. NEVER explicitly mention internal rule labels such as "Condition A", "Condition B", "Pathway A", or "the instruction criteria" in your final output text.
        

        

        Structure your response exactly with these three clean markdown sections:

        # Executive Portfolio Briefing: Resource Allocation & Strategic Alignment

        ## 1. Landscape Overview
        Synthesize the overarching focus of this unique technical intersection. State the total active filtered budget (${total_filtered_budget:,.2f}) upfront. Highlight where capital is heavily migrating versus where investment density is low.

        ## 2. Key Strategic Pillars
        Detail the primary distinct strategic avenues discovered. Integrate the financial metrics seamlessly into the narrative prose for each pillar (e.g., "Accounting for X% of total allocated capital, the second pillar centers on..."). Focus heavily on the scale of capital velocity behind each theme.

        ## 3. Resource Allocation Discrepancies & Strategic Trajectory
        Analyze whether the current distribution of capital is balanced using the following condition based on the current category:

        CRITICAL PRE-FILTER RULE: 
        The user has applied the following explicit search constraints: {query_intersection}.
        If a search constraint is active, DO NOT criticize the portfolio for lacking other diseases
        (e.g., do not say it lacks cardiovascular or infectious disease focus). The user has intentionally isolated this subset. Instead, evaluate the internal allocation discrepancies *within* this restricted search space (e.g., inside this '{query_intersection}' portfolio, how is capital distributed between early-stage discovery vs longitudinal tracking, or high-cost assays vs screening?).

        If the active category intent is APPLIED (Therapeutic, Diagnostic, Clinical / Health Systems, Observation Epidemiology)]
        Evaluate if the distribution of capital aligns with known clinical disease burdens, global prevalence, or patient delivery bottlenecks. Contrast early-stage emerging technology plays against mature, commoditized technologies within this search space (e.g., checking if the portfolio over-allocates to old paradigms vs emerging technical shifts). 

        If the active category intent is FOUNDATIONAL (Mechanistic / Basic Science, Research Tool, Infrastructure, Education / Training)]
        Evaluate the portfolio based on technological maturity, methodological breadth, and platform obsolescence. Identify if the capital is stuck funding legacy baseline frameworks (e.g., traditional mapping techniques or outdated standard assays) or if it is adequately backing next-generation infrastructure platforms (e.g., cross-disciplinary AI integration, automated pipelines, or high-throughput single-cell platforms) necessary to support downstream clinical breakthroughs.

        Address the current active filters directly and do not speak in broad generalities.
        """
        
        final_briefing = client.models.generate_content(model = "gemini-3-flash-preview", contents = reduce_prompt)
        
        return {"summary": final_briefing.text}
            

     
    finally:
        conn.close()