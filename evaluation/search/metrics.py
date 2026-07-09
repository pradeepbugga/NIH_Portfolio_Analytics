import pandas as pd

def compute_metrics(retrieved, ground_truth):
    """
    Compute retrieval metrics against an RCDC portfolio.

    Args:
        retrieved (dict):
            Output from hybrid_search_range().
        ground_truth (pd.DataFrame):
            Ground-truth RCDC portfolio for a single category.

    Returns:
        dict
    """

    # -------------------------
    # Embedding candidates
    # -------------------------

    candidates = retrieved.get("candidates", [])

    candidates_df = pd.DataFrame(
        candidates,
        columns=["grant_id", "vector_similarity"]
    )

    # -------------------------
    # Reranked results
    # -------------------------

    ranked_results = retrieved.get("records", [])

    ranked_df = pd.DataFrame(ranked_results)[
        ["grant_id", "score"]
    ]

    # -------------------------
    # Convert to sets
    # -------------------------

    retrieved_candidates = set(
        candidates_df["grant_id"].astype(str)
    )

    retrieved_ranked = set(
        ranked_df["grant_id"].astype(str)
    )

    ground_truth_set = set(
        ground_truth["grant_id"].astype(str)
    )

    # ==========================================================
    # EMBEDDING
    # ==========================================================

    tp_candidates = retrieved_candidates & ground_truth_set

    fp_candidates = retrieved_candidates - ground_truth_set

    fn_candidates = ground_truth_set - retrieved_candidates

    precision_candidates = (
        len(tp_candidates)
        / len(retrieved_candidates)
        if retrieved_candidates
        else 0
    )

    recall_candidates = (
        len(tp_candidates)
        / len(ground_truth_set)
        if ground_truth_set
        else 0
    )

    # ==========================================================
    # RERANKER
    # ==========================================================

    tp_ranked = retrieved_ranked & ground_truth_set

    fp_ranked = retrieved_ranked - ground_truth_set

    fn_ranked = ground_truth_set - retrieved_ranked

    precision_ranked = (
        len(tp_ranked)
        / len(retrieved_ranked)
        if retrieved_ranked
        else 0
    )

    recall_ranked = (
        len(tp_ranked)
        / len(ground_truth_set)
        if ground_truth_set
        else 0
    )

    # ==========================================================
    # Return
    # ==========================================================

    return {

        "candidates": {

            "precision": precision_candidates,

            "recall": recall_candidates,

            "true_positive": sorted(tp_candidates),

            "false_positive": sorted(fp_candidates),

            "false_negative": sorted(fn_candidates),
        },

        "reranked": {

            "precision": precision_ranked,

            "recall": recall_ranked,

            "true_positive": sorted(tp_ranked),

            "false_positive": sorted(fp_ranked),

            "false_negative": sorted(fn_ranked),
        },
    }



    



