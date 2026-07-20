import pandas as pd
from sentence_transformers import InputExample, CrossEncoder
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from core.search.fill_abstract import add_abstracts
from sentence_transformers.cross_encoder.evaluation import (
    CrossEncoderCorrelationEvaluator,
)

MODEL_VERSION_NUMBER = "v5"
NUM_EPOCHS = 4  # we found 2 epochs to be sufficient for convergence on this dataset
EVALUATION_STEPS = (
    55  # for batch size 4 and 489 train labels, we get almost 110 steps per epoch
)
WARMUP_STEPS = 10  # suitable for our small dataset

# Load and validate data
# Note, we did not include abstracts in the initial CSV for visual clarity, so we need to pull those from the database

df = pd.read_csv("./data/labels_052926.csv")

required_cols = ["query", "grant_id", "title", "disease_label"]
df = df.dropna(subset=required_cols)

df["disease_label"] = pd.to_numeric(df["disease_label"], errors="coerce")

df = df.dropna(subset=["disease_label"])

# Add abstract from SQL
df = add_abstracts(df)


# Prepare training examples
text_cols = ["query", "title", "abstract"]

for col in text_cols:
    df[col] = df[col].fillna("").astype(str)

# Construct document text consistent with serving
df["doc_text"] = df["title"].str.strip() + " " + df["abstract"].str.strip()


examples = [
    InputExample(texts=[row.query, row.doc_text], label=float(row.disease_label))
    for row in df.itertuples(index=False)
]


train_ex, val_ex = train_test_split(examples, test_size=0.1, random_state=42)

# Initialize the CrossEncoder model

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", num_labels=1)

# Train the CrossEncoder model

sentence_pairs = [[ex.texts[0], ex.texts[1]] for ex in val_ex]  # [query, doc]

scores = [float(ex.label) for ex in val_ex]
assert all(
    isinstance(s, float) for s in scores
), f"All scores must be float type, but got: {[type(s) for s in scores]}"

# Initialize the evaluator for the CrossEncoder model to see Spearman and Pearson correlation
evaluator = CrossEncoderCorrelationEvaluator(
    sentence_pairs=sentence_pairs,
    scores=scores,
    name="disease-relevance",
    batch_size=16,
)

model.fit(
    train_dataloader=DataLoader(train_ex, shuffle=True, batch_size=4),
    evaluator=evaluator,
    epochs=NUM_EPOCHS,
    evaluation_steps=EVALUATION_STEPS,
    warmup_steps=WARMUP_STEPS,
    save_best_model=True,
    output_path=f"./models/rerankers/{MODEL_VERSION_NUMBER}",
)

# write labels csv to same folder to keep track of the data used for training
df.to_csv(f"./models/rerankers/{MODEL_VERSION_NUMBER}/labels.csv", index=False)
