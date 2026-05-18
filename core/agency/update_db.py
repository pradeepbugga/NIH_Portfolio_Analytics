# this script adds agency column to db

from core.db.connection import get_db_connection

conn = get_db_connection()

cur = conn.cursor()


batch_size = 50000  # We can use a much bigger batch size since it's efficient
total_updated = 0

print("Starting high-performance batch migration...")

while True:
    # 1. Grab a sub-selection of IDs and update them entirely inside the DB engine
    query = """
        WITH batch AS (
            SELECT grant_id 
            FROM ResearchGrants 
            WHERE agency_code IS NULL 
            LIMIT %s
            FOR UPDATE SKIP LOCKED  -- Prevents blocking your FastAPI web app
        )
        UPDATE ResearchGrants rg
        SET agency_code = SUBSTRING(rg.grant_id, 5, 2)
        FROM batch
        WHERE rg.grant_id = batch.grant_id;
    """
    
    cur.execute(query, (batch_size,))
    rows_affected = cur.rowcount  # Tracks how many rows were updated in this pass
    
    if rows_affected == 0:
        print("\n🎉 All rows updated successfully!")
        break

    conn.commit()  # Commit after each batch to free up locks and resources
        
    total_updated += rows_affected
    print(f"Updated {rows_affected} rows ({total_updated} total strings processed)...")

cur.close()
conn.close()







