from core.db.connection import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

cur.execute("""CREATE INDEX IF NOT EXISTS idx_rg_agency_code ON ResearchGrants (agency_code);""")

cur.execute("""CREATE INDEX IF NOT EXISTS idx_rg_agency_timeline 
ON ResearchGrants (agency_code, fiscal_year, total_award_amount);""")

#cur.execute("""CREATE INDEX IF NOT EXISTS idx_gl_grant_id ON grant_labels (grant_id);""")


#cur.execute("""DROP INDEX idx_rg_agency_timeline;""")

#cur.execute("""CREATE INDEX idx_rg_agency_year ON ResearchGrants (agency_code, fiscal_year);""")

#cur.execute("""VACUUM ANALYZE ResearchGrants;""")

# -- 1. Tell Postgres to use your agency index as the clustering blueprint
cur.execute("""CLUSTER ResearchGrants USING idx_rg_agency_code;""")

#-- 2. Rebuild stats so the query planner knows the data is physically localized
cur.execute("""ANALYZE ResearchGrants;""")

cur.close()
conn.close()