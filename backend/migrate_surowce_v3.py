import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "product_generator.db")

def migrate():
    print(f"Targeting database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    updates = [
        ("Zafiro", "ZAFIRO%"),
        ("Master Martini", "MASTER MARTINI%"),
        ("Owoce liofilizowane", "%LIOFILIZOWAN%"),
        ("Millano", "MILANO%"),
        ("Millano", "MILLANO%")
    ]
    
    for cat, pattern in updates:
        cursor.execute("UPDATE surowce SET kategoria = ? WHERE kategoria = 'Inne' AND UPPER(nazwa) LIKE ?", (cat, pattern))
        if cursor.rowcount > 0:
            print(f"Pattern matched: {pattern} -> {cat} ({cursor.rowcount} rows)")

    conn.commit()
    
    print("\nFinal State of 'Inne':")
    cursor.execute("SELECT nazwa FROM surowce WHERE kategoria = 'Inne'")
    for row in cursor.fetchall():
        print(f" - {row[0]}")
        
    conn.close()

if __name__ == "__main__":
    migrate()
