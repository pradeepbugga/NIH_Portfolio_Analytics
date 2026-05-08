#main.py

from fastapi import FastAPI, Query, Request
from core.db.connection import get_db_connection
from core.search.search_service_prod import semantic_search_range
from core.search.cache import get_cached_results, save_cached_results
from core.search.query_embedding import warmup_query_encoder
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from core.search.modal_reranker import rerank_fn

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
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


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


            return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "query": query,
                "years": years,
                "funding": funding,
                "results": cached_results["records"],
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
        return templates.TemplateResponse(
            "results.html",
           {
            "request": request,
            "query": query,
            "years": years,
            "funding": funding,
            "results": results["records"]
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
            "Mechanistic": row[0] or 0,
            "Therapeutic": row[1] or 0,
            "Diagnostic": row[2] or 0,
            "Research Tool": row[3] or 0,
            "Clinical / Health Systems": row[4] or 0,
            "Infrastructure": row[5] or 0,
            "Education": row[6] or 0,
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

            LIMIT 100
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

@app.get("/api/portfolio/grants/search")
def portfolio_grants_search(
    year: int,
    category: str,
    query: str
):