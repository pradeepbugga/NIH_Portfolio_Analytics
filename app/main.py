#main.py

from fastapi import FastAPI, Query
from db.connection import get_db_connection
from search.search_service_prod import semantic_search_range
from search.cache import get_cached_results, save_cached_results
from core.search.query_embedding import warmup_query_encoder
from core.search.reranker import warmup_reranker
from fastapi.responses import HTMLResponse

app = FastAPI(title="NIH Grant Search API")

def normalize_query(q: str) -> str:
    return " ".join(q.lower().split())


@app.get("/search")

def search(
    query: str = Query(..., description="Search query string")):

    
    # warm up models to reduce initial latency
    warmup_query_encoder()
    warmup_reranker()
    
    #normalize query before searching
    query = normalize_query(query)

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if cached_results := get_cached_results(cur, query):
            return cached_results
    
        #prepare HNSW search parameters
        cur.execute("SET hnsw.ef_search = 1000;")
     
        #perform semantic search
        results = semantic_search_range(query, cur)

        #cache results
        save_cached_results(cur, query, results)
        conn.commit()
        
        return results
    finally:
        conn.close()


@app.get("/", response_class=HTMLResponse)
def home():
    with open("./app/static/index.html") as f:
        return f.read()

