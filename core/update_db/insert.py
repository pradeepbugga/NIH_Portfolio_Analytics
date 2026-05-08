# this script inserts classifiers into the database

import pandas as pd
from core.db.connection import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

df_path = "./data/grant_categories_binary.csv"
df = pd.read_csv(df_path)

# create table if it doesn't exist

cur.execute("""
CREATE TABLE grant_labels (

    grant_id TEXT PRIMARY KEY,

    mechanistic INTEGER DEFAULT 0,
    therapeutic INTEGER DEFAULT 0,
    diagnostic INTEGER DEFAULT 0,
    research_tool INTEGER DEFAULT 0,
    clinical INTEGER DEFAULT 0,
    infrastructure INTEGER DEFAULT 0,
    education INTEGER DEFAULT 0,
    obs_ep INTEGER DEFAULT 0

);
""")

rows = []

for _, row in df.iterrows():

    rows.append((
        str(row["grant_id"]),
        int(row["mechanistic"]),
        int(row["therapeutic"]),
        int(row["diagnostic"]),
        int(row["research_tool"]),
        int(row["clinical"]),
        int(row["infrastructure"]),
        int(row["education"]),
        int(row["obs_ep"])
    ))


cur.executemany("""
    INSERT INTO grant_labels (grant_id, mechanistic, therapeutic, diagnostic, research_tool, clinical, infrastructure, education, obs_ep)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (grant_id) DO UPDATE SET
        mechanistic = EXCLUDED.mechanistic,
        therapeutic = EXCLUDED.therapeutic,
        diagnostic = EXCLUDED.diagnostic,
        research_tool = EXCLUDED.research_tool,
        clinical = EXCLUDED.clinical,
        infrastructure = EXCLUDED.infrastructure,
        education = EXCLUDED.education,
        obs_ep = EXCLUDED.obs_ep;
""", rows)

print(f"Inserted {len(rows)} rows into grant_labels table.")

conn.commit()
conn.close()
