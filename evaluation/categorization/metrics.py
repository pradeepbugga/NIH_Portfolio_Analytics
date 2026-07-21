import pandas as pd


def compute_metrics(predictions_df: pd.DataFrame) -> dict:
    """
    Compute binary classification metrics for a challenge set.

    Required columns:
        grant_id
        expected
        predicted
        reasoning

    expected and predicted should be encoded as:
        1 = YES
        0 = NO
    """

    # -------------------------
    # Validate input
    # -------------------------

    required_columns = {
        "grant_id",
        "expected",
        "predicted",
        "reasoning",
    }

    missing = required_columns - set(predictions_df.columns)

    assert len(missing) == 0, f"Missing required columns: {missing}"

    # Ensure every prediction is valid
    assert predictions_df["predicted"].notnull().all(), (
        "Some GPT predictions are None. " "Check parsing or malformed JSON outputs."
    )

    # -------------------------
    # Confusion matrix
    # -------------------------

    tp = predictions_df[
        (predictions_df["expected"] == 1) & (predictions_df["predicted"] == 1)
    ]

    fp = predictions_df[
        (predictions_df["expected"] == 0) & (predictions_df["predicted"] == 1)
    ]

    fn = predictions_df[
        (predictions_df["expected"] == 1) & (predictions_df["predicted"] == 0)
    ]

    tn = predictions_df[
        (predictions_df["expected"] == 0) & (predictions_df["predicted"] == 0)
    ]

    # -------------------------
    # Metrics
    # -------------------------

    precision = len(tp) / (len(tp) + len(fp)) if (len(tp) + len(fp)) > 0 else 0

    recall = len(tp) / (len(tp) + len(fn)) if (len(tp) + len(fn)) > 0 else 0

    accuracy = (len(tp) + len(tn)) / len(predictions_df)

    f1 = (
        2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    )

    # -------------------------
    # Return
    # -------------------------

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": len(tp),
        "fp": len(fp),
        "fn": len(fn),
        "tn": len(tn),
        # Useful for debugging prompts
        "false_positive": fp,
        "false_negative": fn,
        "true_positive": tp,
        "true_negative": tn,
    }
