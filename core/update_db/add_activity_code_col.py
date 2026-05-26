from core.db.connection import get_db_connection

conn = get_db_connection()

cur = conn.cursor()

print("Altering researchgrants table to add activity_code column...")
cur.execute("ALTER TABLE researchgrants ADD COLUMN IF NOT EXISTS activity_code VARCHAR(3);")
conn.commit()


BATCH_SIZE = 1000
print(f"Beginning to update activity_code column in batches of {BATCH_SIZE}...")

try: 
    #fetch all matching primary key targets
    cur.execute("SELECT grant_id FROM researchgrants WHERE activity_code IS NULL;")

    all_ids = [row[0] for row in cur.fetchall()]
    total_records = len(all_ids)
    print(f"Total records to update: {total_records}")

    # Loop through chunks of primary keys
    for i in range(0, total_records, BATCH_SIZE):
        batch_ids = all_ids[i : i + BATCH_SIZE]
        
        # 1. FIX: Pass a single-item tuple for each row. 
        # (The trailing comma is mandatory to tell Python it's a tuple, not a grouping parenthesis)
        update_data = [(id_val,) for id_val in batch_ids]
        
        # 2. FIX: Use standard positional function syntax substring(column, start, length)
        # This keeps the psycopg2 string formatter completely happy.
        cur.executemany(
            """
            UPDATE researchgrants 
            SET activity_code = substring(grant_id, 2, 3) 
            WHERE grant_id = %s;
            """,
            update_data
        )
        
        # Commit individual batch segments safely
        conn.commit()
        print(f"Processed and committed records {min(i + BATCH_SIZE, total_records)} / {total_records}")

except Exception as e:
    conn.rollback()
    print(f"Migration processing aborted due to execution error: {str(e)}")
    raise e    

print("Database migration completed successfully. Now creating index on activity_code column...")

cur.execute("CREATE INDEX idx_researchgrants_activity_code ON researchgrants(activity_code);")
conn.commit()

print("Index created successfully on activity_code column.")

cur.close()
conn.close()