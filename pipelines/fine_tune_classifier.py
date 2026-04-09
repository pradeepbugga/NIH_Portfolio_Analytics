# in this script, we will train a classifier to predict grant category based on the vector embedding of the title and abstract. 
import pandas as pd
import numpy as np
from core.db.connection import get_db_connection

from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import torch

torch.cuda.empty_cache()
'''

# ---- IMPORT CSV OF LABELED DATA ----
# we have a small dataset of 135 labeled examples that we will use to train the classifier

df = pd.read_csv("./grant_clinical_labels.csv")

# only keep columns 'grant_id' and 'category'
df = df[["grant_id", "category"]].dropna()


def normalize_id(x):
    return x.strip().upper().replace(" ", "")


df["grant_id_norm"] = df["grant_id"].apply(normalize_id)

grant_ids = df["grant_id_norm"].tolist()


# merge categories 'clinical infra', 'clinical outcomes', and 'observational epidemiology' into a single 'clinical' category
df["category"] = df["category"].replace({
    "clinical infra": "clinical",
    "clinical outcomes": "clinical",
    "observational epidemiology": "clinical"
})

# merge categories 'therapeutic platform' and 'research tool' and 'therapeutic' into a single 'therapeutic and tools' category
df["category"] = df["category"].replace({
    "therapeutic platform": "therapeutic and tools",
    "research tool": "therapeutic and tools",
    "therapeutic": "therapeutic and tools",
    "diagnostic": "therapeutic and tools"
})

# print category distribution
print("Category distribution:")
print(df["category"].value_counts())


# convert categories to integners
label_mapping = {
    "mechanistic": 0,
    "clinical": 1,
    "therapeutic and tools": 2,
    "medical device": 3
}

# first strip white space and lowercase then map to integers
df["label"] = df["category"].str.strip().str.lower().map(label_mapping)



#print distribution of labels
print("Label distribution:")
print(df["label"].value_counts())


df = df.dropna(subset=["label"])

def get_all_titles_abstracts(grant_ids):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Normalize IDs for the SQL 'IN' clause
    # This prepares a string like: ('ID1', 'ID2', 'ID3')
    placeholders = ', '.join(['%s'] * len(grant_ids))
    normalized_ids = [normalize_id(gid) for gid in grant_ids]
    
    # 2. Single query to get everything
    query = f"""
        SELECT 
            UPPER(REPLACE(TRIM(grant_id), ' ', '')) as norm_id, 
            project_title, 
            abstract 
        FROM researchgrants 
        WHERE UPPER(REPLACE(TRIM(grant_id), ' ', '')) IN ({placeholders})
    """
    
    cursor.execute(query, normalized_ids)
    results = cursor.fetchall() # Returns a list of (id, title, abstract)
    
    cursor.close()
    conn.close()
    
    # 3. Convert to a lookup dictionary for speed
    return {row[0]: (row[1], row[2]) for row in results}

# --- IMPLEMENTATION ---

# Fetch all at once
grant_data_lookup = get_all_titles_abstracts(df["grant_id"].tolist())

# Map the data back to the dataframe
df["title_abs_tuple"] = df["grant_id_norm"].map(grant_data_lookup)

# Split the tuple into two columns
# Use a default (None, None) if a grant wasn't found in the DB
df[["title", "abstract"]] = pd.DataFrame(
    df["title_abs_tuple"].tolist(), 
    index=df.index
).fillna(value={0: "", 1: ""}) # Replace None with empty strings to avoid concatenation errors

# Drop the temporary tuple column
df = df.drop(columns=["title_abs_tuple"])

df=df.dropna(subset=["title", "abstract"])

# create concatenated title_abstract column

df["text"] = df["title"].str.strip() + " [SEP] " + df["abstract"].str.strip()

df['label'] = df['label'].astype(int)

# write to csv
df.to_csv("./grant_clinical_labels_with_text.csv", index=False)


print("Converted categories to integers:")




'''
df = pd.read_csv("./grant_clinical_labels_with_text.csv")

label_mapping = {
    "mechanistic": 0,
    "clinical": 1,
    "therapeutic and tools": 2,
    "medical device": 3
}

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import Trainer, TrainingArguments
from datasets import Dataset
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from torch.nn import CrossEntropyLoss
from sklearn.metrics import f1_score



class_weights = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(df['label']),
    y=df['label']
)

class_weights = torch.tensor(class_weights, dtype=torch.float)

class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        loss_fct = CrossEntropyLoss(weight=class_weights.to(logits.device))
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


def compute_metrics(pred):
    logits, labels = pred
    predictions = np.argmax(logits, axis=-1)
    return {
        'f1_weighted': f1_score(labels, predictions, average='weighted'),
        'f1_macro': f1_score(labels, predictions, average='macro')
    }

train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label"])

train_dataset = Dataset.from_pandas(train_df[["text", "label"]], preserve_index=False)
val_dataset = Dataset.from_pandas(val_df[["text", "label"]], preserve_index=False)

model_name = "thomas-sounack/BioClinical-ModernBERT-base"

tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length = 768)

train_dataset = train_dataset.map(tokenize, batched=True)
val_dataset = val_dataset.map(tokenize, batched=True)

model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=4)

training_args = TrainingArguments(
    output_dir="./results",
    learning_rate=1e-5,
    per_device_train_batch_size=4,
    num_train_epochs=2,
    gradient_accumulation_steps=4,
    eval_strategy="epoch",
    weight_decay=0.01,
    warmup_ratio=0.1,

    fp16=True,
    dataloader_num_workers=2,
    gradient_checkpointing=True,
    logging_steps=10
)

trainer = WeightedTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics
)

print("Starting training...")

trainer.train()

print("Training complete. Evaluating on training data...")

# test the model on the training data itself since we have so little data, and print classification report and confusion matrix

# 1. Run predictions on the validation set (standard practice)
# Or use train_dataset if you specifically want to see training performance
predictions_output = trainer.predict(val_dataset)

# 2. Get the predicted class indices
y_pred = np.argmax(predictions_output.predictions, axis=1)

# 3. Get the TRUE labels from the same dataset used for prediction
# This ensures the lengths always match (e.g., both are 20 samples)
y_true = predictions_output.label_ids

# 4. Now the lengths will match!
print("Classification Report:")
print(classification_report(y_true, y_pred, zero_division=0))

# Confusion Matrix
print("Confusion Matrix:")
cm = confusion_matrix(y_true, y_pred)
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", 
            xticklabels=label_mapping.keys(), 
            yticklabels=label_mapping.keys())
plt.show()
