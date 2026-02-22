import sqlite3
import os

# Database path from database.py logic
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "product_generator.db")

print(f"Migrating database at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # List of columns to add
    columns_to_add = [
        ("ean_karton", "TEXT"),
        ("kategoria", "TEXT"),
        ("masa_netto", "TEXT"),
        ("image_url", "TEXT")
    ]

    for col_name, col_type in columns_to_add:
        try:
            print(f"Adding column {col_name}...")
            cursor.execute(f"ALTER TABLE produkty ADD COLUMN {col_name} {col_type}")
            print(f"Column {col_name} added successfully.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")

    conn.commit()
    conn.close()
    print("Migration finished successfully!")

except Exception as e:
    print(f"CRITICAL ERROR during migration: {e}")
