import sqlite3
import os

db_path = os.path.join(os.getcwd(), "product_generator.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get existing columns
cur.execute("PRAGMA table_info(surowce)")
columns = [row[1] for row in cur.fetchall()]

new_columns = [
    ("sklad_pl", "TEXT"),
    ("sklad_en", "TEXT"),
    ("sklad_procentowy", "TEXT"),
    ("pochodzenie_skladnikow", "TEXT")
]

for col_name, col_type in new_columns:
    if col_name not in columns:
        print(f"Adding column {col_name}...")
        cur.execute(f"ALTER TABLE surowce ADD COLUMN {col_name} {col_type}")

conn.commit()
conn.close()
print("Database schema updated.")
