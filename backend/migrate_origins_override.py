"""
Migracja: dodanie kolumny origins_override do tabeli produkty.
Przechowuje JSON z ręcznie edytowaną listą [{name, percent, countries}].

Uruchomienie jednorazowe: python migrate_origins_override.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "product_generator.db")


def run():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(produkty)")
    cols = [row[1] for row in cur.fetchall()]

    if "origins_override" not in cols:
        cur.execute("ALTER TABLE produkty ADD COLUMN origins_override TEXT")
        print("Kolumna origins_override dodana.")
    else:
        print("Kolumna origins_override już istnieje.")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    run()
