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

    # loop through 
    for i in range(0, total_records, BATCH_SIZE):
        batch_ids = all_ids[i:i+BATCH_SIZE]
        print(f"Processing batch {i//BATCH_SIZE + 1} with {len(batch_ids)} records...")

        update_data = [(id_val, id_val) for id_val in batch_ids]

        cur.executemany("""
        UPDATE researchgrants 
        SET activity_code = SUBSTRING(grant_id FROM 2 FOR 3) 
        WHERE grant_id = %s;"
        """, 
        update_data
        )
        conn.commit()
        print(f"Batch {i//BATCH_SIZE + 1} updated successfully.")

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