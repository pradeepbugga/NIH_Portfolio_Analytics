# this script contains helpers for caching search results
import json
from datetime import date, datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def get_cached_results(cur, query):
    cur.execute(
        "SELECT results FROM cached_searches WHERE query = %s",
        (query,)
    )
    row = cur.fetchone()
    return row[0] if row else None

def save_cached_results(cur, query, results):
    version = results.get("model_version", "v1")

    cur.execute(
        """
        INSERT INTO cached_searches (query, model_version, results, n_results)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (query, model_version)
        DO UPDATE SET
            results = EXCLUDED.results,
            n_results = EXCLUDED.n_results,
            created_at = now()
        """,
        (
            query,
            version,
            json.dumps(results, default=json_serial),
            len(results.get("projects", [])),
        )
    )