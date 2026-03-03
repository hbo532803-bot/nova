import sqlite3

conn = sqlite3.connect("backend/nova.db")  # agar nova.db root me hai to sirf "nova.db" likho
cursor = conn.cursor()

columns = [
    "ALTER TABLE economic_experiments ADD COLUMN status TEXT DEFAULT 'IDEA';",
    "ALTER TABLE economic_experiments ADD COLUMN validation_score REAL DEFAULT 0;",
    "ALTER TABLE economic_experiments ADD COLUMN revenue_generated REAL DEFAULT 0;",
    "ALTER TABLE economic_experiments ADD COLUMN iteration INTEGER DEFAULT 1;",
    "ALTER TABLE economic_experiments ADD COLUMN last_tested TIMESTAMP;"
]

for query in columns:
    try:
        cursor.execute(query)
        print("Added:", query)
    except Exception as e:
        print("Skipped:", e)

conn.commit()
conn.close()

print("DB upgrade complete.")