import json
import os
import time

import anyio

from core.db.connection import get_db_connection
from core.db.cache import get_cached_results, save_cached_results
from core.search.hybrid import hybrid_search_range
from services.formatting import extract_funding, extract_ontology_distribution, format_output_grants



def normalize_query(q: str) -> str:
    """Remove extra whitespace and convert to lowercase for consistent query processing."""
    return " ".join(q.lower().split())

def save_debug_json(path: str, formatted_records: list[dict]):
    """Saves the formatted results to a JSON file for debugging purposes."""
    with open(path, "w") as f:
        json.dump(formatted__records, f, indent=4)


async def search(query: str, synonym_registry: dict):

    query = normalize_query(query)

    conn = await anyio.to_thread.run_sync(get_db_connection)
    cur = conn.cursor()

    debug_path = Path("outputs") / "debug" / "processed_results.json"


    try: 
        cached_results = await anyio.to_thread.run_sync(get_cached_results, cur, query)

        if cached_results:
            print(f"Cache hit for query '{query}'")
            results = cached_results
        
        else:
            print(f"Cache miss for query '{query}'")
            results = await hybrid_search_range(query, cur, rerank_fn=distributed_rerank_fn, synonym_registry=synonym_registry)

            await anyio.to_thread.run_sync(save_cached_results, cur, query, results)
            await anyio.to_thread.run_sync(conn.commit)

        years, funding = extract_funding(results)
        ontology_labels, ontology_values = extract_ontology_distribution(results)

        formatted_records = await anyio.to_thread.run_sync(format_output_grants, results["records"])

        await anyio.to_thread.run_sync(save_debug_json, debug_path, formatted_records)

        return {
            "query": query,
            "years": years,
            "funding": funding,
            "results": formatted_records,
            "ontology_labels": ontology_labels,
            "ontology_values": ontology_values
        }

    finally:
        await anyio.to_thread.run_sync(cur.close)
        await anyio.to_thread.run_sync(conn.close)








@app.get("/search")
async def search(request: Request,
    query: str = Query(..., description="Search query string")):
    """
    Handles the semantic search endpoint, performing query embedding, candidate retrieval, reranking, and result formatting.
    """

    t_start = time.perf_counter()
    print("\n" + "="*50)
    print("=== STARTING DETAILED LATENCY BENCHMARK ===")
    print("="*50)
   
 
    # 1.normalize query before searching
    query = normalize_query(query)
    t_query = time.perf_counter()
    print(f"✅ Query normalized: '{query}' (Latency: {t_query - t_start:.4f}s)")

    # 2. Delegate database connection to a thread-safe context to avoid blocking the event loop
    conn = await anyio.to_thread.run_sync(get_db_connection)
    cur = conn.cursor()

    processed_results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "processed_results.json")


    try:
        t_db_start = time.perf_counter()

        cached_results = await anyio.to_thread.run_sync(get_cached_results, cur, query)

        if cached_results:
            print(f"✅ Cache hit for query '{query}'")
            years, funding = extract_funding(cached_results)
            ontology_labels, ontology_values = extract_ontology_distribution(cached_results)
            
            # delegate the formatting to a thread-safe context to avoid blocking the event loop
            formatted_cached_records = await anyio.to_thread.run_sync(format_output_grants, cached_results["records"]) 

            
            await anyio.to_thread.run_sync(save_debug_json)

            print(f"✅ Cached results formatted and saved to disk for inspection (Latency: {time.perf_counter() - t_db_start:.4f}s)")

            return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "query": query,
                "years": years,
                "funding": funding,
                "results": formatted_cached_records,
                "ontology_labels": ontology_labels,
                "ontology_values": ontology_values
            }
            )

        # ================================================================
        # CACHE MISS: Proceed with full hybrid search pipeline
        # ================================================================


        # A. DATABASE TUNING AND VECTOR SCAN RETRIEVAL
        t_db_mid = time.perf_counter()
        print(f"✅ Database ready for search (Latency: {t_db_mid - t_db_start:.4f}s)")

        # execute the vector retrieval in a thread-safe context to avoid blocking the event loop
        results = await hybrid_search_range(query, cur, rerank_fn=distributed_rerank_fn, synonym_registry=GLOBAL_SYNONYM_REGISTRY)

        t_db_end = time.perf_counter()
        print(f"✅ Hybrid search completed (Latency: {t_db_end - t_db_mid:.4f}s)")


        # B. WRITE BACK TO CACHE: Save the results to Postgres for future queries
        t_cache_start = time.perf_counter()
        await anyio.to_thread.run_sync(save_cached_results, cur, query, results)
        await anyio.to_thread.run_sync(conn.commit)
        print(f"✅ Results cached (Latency: {time.perf_counter() - t_cache_start:.4f}s)")
        
        # C. POST-PROCESSING: Extract funding and ontology distributions, format results for frontend
        t_format_start = time.perf_counter()
        years, funding = extract_funding(results)
        ontology_labels, ontology_values = extract_ontology_distribution(results)

        formatted_live_records = await anyio.to_thread.run_sync(format_output_grants, results["records"])
        print(f"✅ Results formatted for frontend (Latency: {time.perf_counter() - t_format_start:.4f}s)")

        # D. LOCAL DEBUGGING: Save the formatted results to disk for inspection
        t_disk_start = time.perf_counter()

        def save_live_json():
            with open(processed_results_path, "w") as f:
                json.dump(formatted_live_records, f, indent=4)
        await anyio.to_thread.run_sync(save_live_json)

        
        print(f"✅ Results saved to disk for inspection (Latency: {time.perf_counter() - t_disk_start:.4f}s)")  

        t_end = time.perf_counter()
        print(f"✅ Total search latency: {t_end - t_start:.4f}s")


        return templates.TemplateResponse(
            "results.html",
           {
            "request": request,
            "query": query,
            "years": years,
            "funding": funding,
            "results": formatted_live_records,
            "ontology_labels": ontology_labels,
            "ontology_values": ontology_values
            }
    )
    finally:
        await anyio.to_thread.run_sync(cur.close)
        await anyio.to_thread.run_sync(conn.close)
