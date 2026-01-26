# abstract_tokens.py
# this script calculates the token counts for NIH grant abstracts using the PubMedBERT tokenizer
# this is important as the limit of tokens for pubmedbert is 512

from core.db.connection import get_sqlalchemy_engine
import numpy as np
import pandas as pd
from transformers import AutoTokenizer

MAX_LEN = 512


# get a sample of 10,000 NIH grants with non-null abstracts
with get_sqlalchemy_engine().connect() as connection:
    df = pd.read_sql("""
        SELECT grant_id, project_title, abstract
    FROM ResearchGrants
    WHERE abstract IS NOT NULL
    ORDER BY random()
    LIMIT 10000;""", connection)

df["word_count"] = df["abstract"].apply(lambda x: len(x.split()))

df["word_count"].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95, 0.99])

tokenizer = AutoTokenizer.from_pretrained("NeuML/pubmedbert-base-embeddings")

tokenizer = AutoTokenizer.from_pretrained("michiyasunaga/BioLinkBERT-base")

def count_tokens(text):
    return len(
        tokenizer.encode(
            text,
            add_special_tokens=True,
            truncation=False
        )
    )

df["token_count"] = df["abstract"].apply(count_tokens)

print(df["token_count"].describe(
    percentiles=[0.5, 0.75, 0.9, 0.95, 0.99]
))

MAX_LEN = 512

fraction_truncated = (df["token_count"] > MAX_LEN).mean()
print(f"Fraction truncated at {MAX_LEN}: {fraction_truncated:.2%}")