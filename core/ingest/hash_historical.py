#hash_historical.py
#this script generates SHA-256 hashes for historical NIH grant records that do not yet have a content hash

import hashlib
import json
from core.db.connection import get_db_connection

#connect to the PostgreSQL database
conn = get_db_connection()
read_cur = conn.cursor(name ="read_cursor", withhold=True)


#loop through each grant record in SQL db in batches, generate hash, and update the record
read_cur.execute("""
    SELECT grant_id, project_title, abstract, phr, total_award_amount 
    FROM researchgrants 
    WHERE content_hash IS NULL
    """)

BATCH_SIZE = 1000
updated = 0

write_cur = conn.cursor()

while True:
    rows = read_cur.fetchmany(BATCH_SIZE)
    print(f"Processing batch of {len(rows)} rows")
    if not rows:
        break

    for grant_id, title, abstract, phr, award in rows:
        payload = {
            "title": title or "",
            "abstract": abstract or "",
            "phr": phr or "",
            "award": float(award) if award is not None else 0.0
        }

        payload_str = json.dumps(payload, sort_keys=True)
        content_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        write_cur.execute(
            """
            UPDATE researchgrants
            SET content_hash = %s,
                record_updated_at = NOW()
            WHERE grant_id = %s
            """,
            (content_hash, grant_id)
        )
        updated += 1

    conn.commit()
    print(f"Updated {updated} rows so far")

read_cur.close()
write_cur.close()
conn.close()