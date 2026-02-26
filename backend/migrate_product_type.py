"""
Migracja: dodanie kolumny product_type do tabeli produkty
i automatyczne przypisanie na podstawie nazwy.

Uruchomienie jednorazowe: python migrate_product_type.py
"""
import sqlite3
import os
import re

# Baza leży w katalogu nadrzędnym względem backend/ (zgodnie z database.py)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "product_generator.db")


def classify_by_name(nazwa: str) -> str:
    name = (nazwa or "").lower()
    if re.search(r'\blizak', name):
        return "lizaki"
    if re.search(r'\bfigurek|\bfigurk', name):
        return "figurki"
    if re.search(r'\btabliczk', name):
        return "tabliczki"
    return "inne"


def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Sprawdź czy kolumna już istnieje
    cur.execute("PRAGMA table_info(produkty)")
    cols = [row[1] for row in cur.fetchall()]

    if "product_type" not in cols:
        cur.execute("ALTER TABLE produkty ADD COLUMN product_type TEXT DEFAULT 'inne'")
        print("Kolumna product_type dodana.")
    else:
        print("Kolumna product_type już istnieje.")

    # Automatyczne przypisanie dla istniejących produktów
    cur.execute("SELECT ean, nazwa_pl FROM produkty")
    rows = cur.fetchall()

    updated = 0
    for ean, nazwa_pl in rows:
        pt = classify_by_name(nazwa_pl)
        cur.execute(
            "UPDATE produkty SET product_type = ? WHERE ean = ?",
            (pt, ean)
        )
        updated += 1

    conn.commit()
    conn.close()
    print(f"Zaktualizowano {updated} produktów.")


if __name__ == "__main__":
    run()
