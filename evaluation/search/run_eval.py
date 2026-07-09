import pandas as pd
import asyncio
import json

from core.db.connection import get_db_connection
from core.search.modal_reranker import distributed_rerank_fn

from core.search.search_service_prod import hybrid_search_range

from evaluation.search.metrics import compute_metrics
from evaluation.search.rcdc import load_rcdc_portfolio

async def main():

    # load benchmark data
    benchmark = pd.read_csv("./evaluation/search/benchmark.csv")

    summary = []

    conn = get_db_connection()
    cur = conn.cursor()

    json_path = "./core/search/rcdc_synonyms.json"
    with open(json_path, "r") as f:
        GLOBAL_SYNONYM_REGISTRY = json.load(f)

    for category in benchmark["category"]:

        print(f"\n========== {category} ==========\n")
        # perform hybrid search for the category

        query = category.replace("_", " ")

        if category in ["HIV_AIDS"]:
            # replace underscore with slash
            query = category.replace("_", "/")

        results = await hybrid_search_range(query=query, cur=cur, rerank_fn=distributed_rerank_fn, synonym_registry=GLOBAL_SYNONYM_REGISTRY, fiscal_years=[2025])

        print(f"Retrieved {len(results['projects'])} projects for category '{category}'.")

        # load ground truth for the category
        ground_truth = load_rcdc_portfolio(category)

        # compute metrics
        metrics = compute_metrics(results, ground_truth)

        summary.append({

            "category": category,

            "n_ground_truth": len(ground_truth),

            "embedding_precision": metrics["candidates"]["precision"],
            "embedding_recall": metrics["candidates"]["recall"],

            "reranker_precision": metrics["reranked"]["precision"],
            "reranker_recall": metrics["reranked"]["recall"],

            "embedding_tp": len(metrics["candidates"]["true_positive"]),
            "embedding_fp": len(metrics["candidates"]["false_positive"]),
            "embedding_fn": len(metrics["candidates"]["false_negative"]),

            "reranker_tp": len(metrics["reranked"]["true_positive"]),
            "reranker_fp": len(metrics["reranked"]["false_positive"]),
            "reranker_fn": len(metrics["reranked"]["false_negative"]),

        })

    summary_df = pd.DataFrame(summary)

    summary_df.to_csv(
        "./evaluation/search/reports/summary.csv",
        index=False
    )

    print("\n========== Overall ==========\n")

    print(summary_df[[
        "embedding_precision",
        "embedding_recall",
        "reranker_precision",
        "reranker_recall"
    ]].mean())

if __name__ == "__main__":
    asyncio.run(main())


