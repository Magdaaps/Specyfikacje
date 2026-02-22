import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "product_generator.db")

# Reorganization target
TARGET_MAPPING = {
    "Zafiro": [
        "ZAFIRO WHITE - POLEWA MLECZNA",
        "ZAFIRO WHITE – POLEWA MLECZNA",
        "ZAFIRO MILK - POLEWA MLECZNO KAKAOWA",
        "ZAFIRO MILK – POLEWA MLECZNO KAKAOWA",
        "ZAFIRO CACAO - POLEWA KAKAOWA",
        "ZAFIRO CACAO – POLEWA KAKAOWA"
    ],
    "Master Martini": [
        "MASTER MARTINI CZEKOLADA MLECZNA 32%",
        "MASTER MARTINI CZEKOLADA CIEMNA",
        "MASTER MARTINI CZEKOLADA BIAŁA"
    ],
    "Owoce liofilizowane": [
        "CZARNA PORZECZKA LIOFILIZOWANA",
        "CZERWONA PORZECZKA LIOFILIZOWANA",
        "MALINA LIOFILIZOWANA",
        "ŻURAWINA LIOFILIZOWANA",
        "JABŁKO LIOFILIZOWANE BEZ SKÓRKI"
    ],
    "Millano": [
        "MILANO CZEKOLADA BIAŁA Z E",
        "MILANO CZEKOLADA Z E 50%",
        "MILANO CZEKOLADA MLECZNA 30% Z E"
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
        
        # We use UPPER(nazwa) to match more reliably and swap common dashes
        for category, items in TARGET_MAPPING.items():
            for item_name in items:
                # Normalize dash to match both in query
                normalized_name = item_name.replace(" – ", " - ").upper()
                
                # Update using LIKE and OR to catch variations
                query = """
                UPDATE surowce 
                SET kategoria = ? 
                WHERE UPPER(nazwa) = ? 
                   OR UPPER(REPLACE(nazwa, ' – ', ' - ')) = ?
                """
                cursor.execute(query, (category, item_name.upper(), normalized_name))
                if cursor.rowcount > 0:
                    print(f"Updated: {item_name} -> {category}")
                else:
                    # Try keyword match if exact fails
                    search_pattern = item_name.split(' - ')[0].split(' – ')[0]
                    keyword_query = """
                    UPDATE surowce 
                    SET kategoria = ? 
                    WHERE kategoria = 'Inne' AND UPPER(nazwa) LIKE ?
                    """
                    # We only do keyword match for very specific ones if they are still in 'Inne'
                    # To avoid over-matching
                    if "ZAFIRO" in search_pattern or "MASTER MARTINI" in search_pattern or "LIOFILIZOWANA" in item_name:
                         # For liofilizowane, match by the fruit name + liofilizowana
                         cursor.execute(keyword_query, (category, f"%{search_pattern.upper()}%"))
                         if cursor.rowcount > 0:
                             print(f"Keyword matched: {search_pattern} -> {category}")

        conn.commit()
        
        # Verify result
        print("\nFinal State of 'Inne':")
        cursor.execute("SELECT nazwa FROM surowce WHERE kategoria = 'Inne'")
        for row in cursor.fetchall():
            print(f" - {row[0]}")
            
        conn.close()
        print("\nReorganization completed.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
