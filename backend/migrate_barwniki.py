import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "product_generator.db")

NEW_MATERIALS = [
    "barwnik: E120",
    "barwnik: E160c",
    "barwnik: E100",
    "barwnik: spirulina",
    "barwnik: E141(i)",
    "barwnik: ekstrakt z buraka"
]
CATEGORY = "Barwniki"

def add_barwniki():
    print(f"Targeting database at: {db_path}")
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if materials exist and update or insert
        for name in NEW_MATERIALS:
            cursor.execute("SELECT id FROM surowce WHERE nazwa = ?", (name,))
            result = cursor.fetchone()
            
            if result:
                cursor.execute("UPDATE surowce SET kategoria = ? WHERE id = ?", (CATEGORY, result[0]))
                print(f"Updated category for: {name}")
            else:
                # Insert new material with default values
                cursor.execute("""
                    INSERT INTO surowce (
                        nazwa, kategoria, energia_kj, energia_kcal, tluszcz, kwasy_nasycone, 
                        weglowodany, cukry, bialko, sol, blonnik, 
                        alergen_gluten, alergen_skorupiaki, alergen_jaja, alergen_ryby, 
                        alergen_orzeszki_ziemne, alergen_soja, alergen_mleko, alergen_orzechy, 
                        alergen_seler, alergen_gorczyca, alergen_sezam, alergen_dwutlenek_siarki, 
                        alergen_lubin, alergen_mieczaki
                    ) VALUES (
                        ?, ?, 0, 0, 0, 0, 
                        0, 0, 0, 0, 0, 
                        'Nie zawiera', 'Nie zawiera', 'Nie zawiera', 'Nie zawiera', 
                        'Nie zawiera', 'Nie zawiera', 'Nie zawiera', 'Nie zawiera', 
                        'Nie zawiera', 'Nie zawiera', 'Nie zawiera', 'Nie zawiera', 
                        'Nie zawiera', 'Nie zawiera'
                    )
                """, (name, CATEGORY))
                print(f"Added new material: {name}")
        
        conn.commit()
        conn.close()
        print("Migration completed successfully.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    add_barwniki()
