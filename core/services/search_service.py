import json
import os
import time
from pathlib import Path

import anyio

from core.db.connection import get_db_connection
from core.search.cache import get_cached_results, save_cached_results
from core.search.hybrid import hybrid_search_range
from core.services.formatting import extract_funding, extract_ontology_distribution, format_output_grants



def normalize_query(q: str) -> str:
    """Remove extra whitespace and convert to lowercase for consistent query processing."""
    return " ".join(q.lower().split())

def save_debug_json(path: str, formatted_records: list[dict]):
    """Saves the formatted results to a JSON file for debugging purposes."""
    with open(path, "w") as f:
        json.dump(formatted_records, f, indent=4)


async def search(query: str, rerank_fn, synonym_registry: dict) -> dict:

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
            results = await hybrid_search_range(query, cur, rerank_fn=rerank_fn, synonym_registry=synonym_registry)

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
