# this script contains helpers for caching search results
import json

def get_cached_results(cur, query):
    cur.execute(
        "SELECT results FROM cached_searches WHERE query = %s",
        (query,)
    )
    row = cur.fetchone()
    return row[0] if row else None

def save_cached_results(cur, query, results):
    cur.execute(
        """
        INSERT INTO cached_searches (query, results)
        VALUES (%s, %s)
        ON CONFLICT (query) DO UPDATE
        SET results = EXCLUDED.results,
            created_at = now()
        """,
        (query, json.dumps(results))
    )