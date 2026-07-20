import pandas as pd
from core.db.connection import get_db_connection
from evaluation.categorization.grant_loader import load_grant_texts
from evaluation.categorization.classify import classify_grant_text
from evaluation.categorization.metrics import compute_metrics
from tqdm import tqdm

from dotenv import load_dotenv

load_dotenv()

category = "research_tool"


benchmark = pd.read_csv(f"./evaluation/categorization/challenge_sets/{category}.csv")
prompt_path = f"./core/llm/prompts/{category}.txt"

with open(prompt_path, "r") as f:
    prompt = f.read()

conn = get_db_connection()
cur = conn.cursor()

docs = load_grant_texts(cur, benchmark["grant_id"].tolist())

conn.close()

predictions = []

for _, row in tqdm(
    benchmark.iterrows(), total=len(benchmark), desc="Classifying grants"
):
    grant_id = row["grant_id"]
    expected = row["label"]

    doc = docs[grant_id]

    title = doc["title"]
    abstract = doc["abstract"]

    result = classify_grant_text(title, abstract, prompt)

    if result["answer"].lower().strip() == "yes":
        predicted = 1
    elif result["answer"].lower().strip() == "no":
        predicted = 0
    else:
        print(f"Unexpected answer for grant {grant_id}: {result['answer']}")
        predicted = None

    predictions.append(
        {
            "grant_id": grant_id,
            "expected": expected,
            "predicted": predicted,
            "reasoning": result["reasoning"],
        }
    )

predictions_df = pd.DataFrame(predictions)

predictions_df.to_csv(
    f"./evaluation/categorization/reports/{category}_predictions.csv", index=False
)

metrics = compute_metrics(predictions_df)

print(metrics)

metrics["false_positive"].to_csv(
    f"./evaluation/categorization/reports/{category}_false_positive.csv",
    index=False,
)

metrics["false_negative"].to_csv(
    f"./evaluation/categorization/reports/{category}_false_negative.csv",
    index=False,
)
