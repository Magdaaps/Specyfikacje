import sqlite3
import os

# The app uses product_generator.db in the root folder based on database.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "product_generator.db")

def migrate():
    print(f"Targeting database at: {db_path}")
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        columns = [
            ("warunki_przechowywania", "TEXT"),
            ("termin_przydatnosci", "TEXT"),
            ("wyrazenie_format_daty", "TEXT"),
            ("informacje_dodatkowe", "TEXT")
        ]
        
        for col_name, col_type in columns:
            try:
                cursor.execute(f"ALTER TABLE produkty ADD COLUMN {col_name} {col_type}")
                print(f"Added column {col_name}")
            except sqlite3.OperationalError as e:
                print(f"Skipping column {col_name}: {e}")
        
        conn.commit()
        conn.close()
        print("Migration completed successfully.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
