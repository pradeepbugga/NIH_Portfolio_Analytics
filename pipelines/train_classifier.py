# in this script, we will train a classifier to predict grant category based on the vector embedding of the title and abstract. 
import pandas as pd
import numpy as np
from core.db.connection import get_db_connection

from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# ---- IMPORT CSV OF LABELED DATA ----
# we have a small dataset of 135 labeled examples that we will use to train the classifier

df = pd.read_csv("./grant_clinical_labels.csv")

# only keep columns 'grant_id' and 'category'
df = df[["grant_id", "category"]].dropna()

# ---- ADD EMBEDDINGS ----
# we will pull the embeddings from the database via the grant_id, which is the primary key in the embeddings table

def normalize_id(x):
    return x.strip().upper().replace(" ", "")

def get_embeddings(grant_ids):
    conn = get_db_connection()
    cursor = conn.cursor()
    format_strings = ",".join(["%s"] * len(grant_ids))
    query = f"SELECT grant_id, embedding FROM grantembeddings WHERE UPPER(REPLACE(TRIM(grant_id), ' ', '')) IN ({format_strings})"
    cursor.execute(query, tuple(grant_ids))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return {grant_id: embedding for grant_id, embedding in results}

df["grant_id_norm"] = df["grant_id"].apply(normalize_id)

grant_ids = df["grant_id_norm"].tolist()

embeddings_dict = get_embeddings(grant_ids)

# add embedding column to dataframe
df["embedding"] = df["grant_id_norm"].map(embeddings_dict)

# print any rows where embedding is missing
missing_embeddings = df[df["embedding"].isna()]
if not missing_embeddings.empty:
    print("Warning: Missing embeddings for the following grant_ids:")
    print(missing_embeddings["grant_id_norm"].tolist())

# remove missing embeddings
df = df.dropna(subset=["embedding"])

# print length
print(f"Number of examples with embeddings: {len(df)}")



# convert embedding from string to numpy array
import ast
def parse_embedding(embedding_str):
    try:
        return np.array(ast.literal_eval(embedding_str))
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing embedding: {e}")
        return None
df["embedding"] = df["embedding"].apply(parse_embedding)

#print number of examples in each category
#print("Category distribution:")
#print(df["category"].value_counts())

# ---- TRAIN CLASSIFIER ----

# standard scaling of embeddings
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X = np.vstack(df["embedding"].values)
X_scaled = scaler.fit_transform(X)

# set up train test split maintaining class balance
from sklearn.model_selection import train_test_split, cross_val_predict
y = df["category"].values
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)   

# set up linear SVM
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV

# build pipeline
base_svc = LinearSVC(class_weight="balanced", dual=False, C=1.0, max_iter=10000)
from sklearn.neighbors import KNeighborsClassifier

# k=3 or k=5 is ideal for N=115
# metric='cosine' is the KEY here for PubMedBERT
pipeline = Pipeline([
    ("scaler", StandardScaler()), # Still good practice
    ("clf", KNeighborsClassifier(n_neighbors=3, metric='cosine', weights='distance'))
])

y_pred = cross_val_predict(pipeline, X, y, cv=5)

# 4. Evaluate the results
print("Classification Report (Leave-One-Out / Cross-Validation):")
print(classification_report(y, y_pred, zero_division=0))

# 5. Confusion Matrix
plt.figure(figsize=(10, 8))
cm = confusion_matrix(y, y_pred)
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", 
            xticklabels=np.unique(y), yticklabels=np.unique(y))
plt.xlabel("Predicted")
plt.ylabel("True")
plt.title("Confusion Matrix (Full Dataset via Cross-Validation)")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()
