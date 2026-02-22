import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "product_generator.db")

def check_materials():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    search_terms = ["E120", "E160c", "E100", "spirulina", "E141", "burak"]
    
    print("Searching for materials:")
    for term in search_terms:
        cursor.execute("SELECT id, nazwa, kategoria FROM surowce WHERE UPPER(nazwa) LIKE ?", (f"%{term.upper()}%",))
        results = cursor.fetchall()
        if results:
            for r in results:
                print(f"Found: ID={r[0]}, Name={r[1]}, Category={r[2]}")
        else:
            print(f"Not found: {term}")
            
    conn.close()

if __name__ == "__main__":
    check_materials()
