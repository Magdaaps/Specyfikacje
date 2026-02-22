import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "product_generator.db")

MAPPING = {
    "Master Martini": [
        "MASTER MARTINI CZEKOLADA MLECZNA 32%",
        "MASTER MARTINI CZEKOLADA CIEMNA",
        "MASTER MARTINI CZEKOLADA BIAŁA"
    ],
    "Zafiro": [
        "ZAFIRO WHITE – POLEWA MLECZNA",
        "ZAFIRO MILK – POLEWA MLECZNO KAKAOWA",
        "ZAFIRO CACAO – POLEWA KAKAOWA"
    ],
    "Millano": [
        "MILLANO CZEKOLADA BIAŁA 29%",
        "MILLANO CZEKOLADA 45%",
        "MILLANO CZEKOLADA MLECZNA 30%",
        "MILANO CZEKOLADA 33%",
        "MILANO CZEKOLADA BIAŁA Z E",
        "MILANO CZEKOLADA Z E 50%",
        "MILANO CZEKOLADA MLECZNA 30% Z E",
        "MILANO POLEWA KAKAOWO MLECZNA"
    ],
    "Wiepol": [
        "KREM MILK WIEPOL",
        "WIEPOL KREM O SMAKU TRUSKAWKOWYM"
    ],
    "Owoce liofilizowane": [
        "CZARNA PORZECZKA LIOFILIZOWANA",
        "CZERWONA PORZECZKA LIOFILIZOWANA",
        "MALINA LIOFILIZOWANA",
        "ŻURAWINA LIOFILIZOWANA",
        "JABŁKO LIOFILIZOWANE BEZ SKÓRKI"
    ]
}

def migrate():
    print(f"Targeting database at: {db_path}")
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add column if not exists
        try:
            cursor.execute("ALTER TABLE surowce ADD COLUMN kategoria TEXT")
            print("Added column kategoria to surowce")
        except sqlite3.OperationalError:
            print("Column kategoria already exists")
        
        # Set default to 'Inne' for all
        cursor.execute("UPDATE surowce SET kategoria = 'Inne' WHERE kategoria IS NULL")
        
        # Apply mapping
        for category, items in MAPPING.items():
            for item_name in items:
                cursor.execute("UPDATE surowce SET kategoria = ? WHERE nazwa = ?", (category, item_name))
        
        conn.commit()
        conn.close()
        print("Migration and mapping completed successfully.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
