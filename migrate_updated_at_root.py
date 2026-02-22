import sqlite3
import os

root_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(root_dir, "product_generator.db")

print(f"Migrating database at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 1: Add the column without a default
    try:
        print("Adding column updated_at...")
        cursor.execute("ALTER TABLE produkty ADD COLUMN updated_at DATETIME")
        print("Column updated_at added successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column updated_at already exists.")
        else:
            raise e

    # Step 2: Set current timestamp for existing rows
    print("Updating existing rows with current timestamp...")
    cursor.execute("UPDATE produkty SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
    
    conn.commit()
    conn.close()
    print("Migration finished successfully!")

except Exception as e:
    print(f"CRITICAL ERROR during migration: {e}")
