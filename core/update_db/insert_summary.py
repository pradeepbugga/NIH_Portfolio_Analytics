import json
from core.db.connection import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS grant_summaries (
    grant_id TEXT PRIMARY KEY,
    two_sentence_summary TEXT NOT NULL,
    summary_llm_model TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

with open("./gpt_summary/gpt_results_2025_summary_part_1_parsed.jsonl", "r") as f:
    for line in f:
        grant_id = json.loads(line)["grant_id"]
        two_sentence_summary = json.loads(line)["summary"]
        summary_llm_model = 'gpt-5.4-nano, medium effort reasoning'
        cur.execute("""
            INSERT INTO grant_summaries (grant_id, two_sentence_summary, summary_llm_model)
            VALUES (%s, %s, %s)
            ON CONFLICT (grant_id) DO UPDATE SET
                two_sentence_summary = EXCLUDED.two_sentence_summary,
                summary_llm_model = EXCLUDED.summary_llm_model,
                updated_at = CURRENT_TIMESTAMP;
        """, (grant_id, two_sentence_summary, summary_llm_model))

with open("./gpt_summary/gpt_results_2025_summary_part_2_parsed.jsonl", "r") as f:
    for line in f:
        grant_id = json.loads(line)["grant_id"]
        two_sentence_summary = json.loads(line)["summary"]
        summary_llm_model = 'gpt-5.4-nano, medium effort reasoning'
        cur.execute("""
            INSERT INTO grant_summaries (grant_id, two_sentence_summary, summary_llm_model)
            VALUES (%s, %s, %s)
            ON CONFLICT (grant_id) DO UPDATE SET
                two_sentence_summary = EXCLUDED.two_sentence_summary,
                summary_llm_model = EXCLUDED.summary_llm_model,
                updated_at = CURRENT_TIMESTAMP;
        """, (grant_id, two_sentence_summary, summary_llm_model))

conn.commit()
cur.close()



