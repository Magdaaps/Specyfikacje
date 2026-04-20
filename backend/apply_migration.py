"""
Aplikuje supabase_schema.sql i supabase_data.sql do Supabase PostgreSQL.
Uruchom: venv/Scripts/python apply_migration.py
"""
import os, sys, re
import psycopg2
from psycopg2 import sql

# ---- Konfiguracja ----
# Próbujemy bezpośrednie połączenie (port 5432)
# Jeśli nie działa, użyj POOLER_URL z dashboardu Supabase
DB_URL = os.getenv("DATABASE_URL", "")

script_dir = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(script_dir, "supabase_schema.sql")
DATA_FILE   = os.path.join(script_dir, "supabase_data.sql")

def run_sql_file(conn, filepath, label):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Podziel na pojedyncze instrukcje – ignoruj puste linie i komentarze
    statements = []
    current = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            if current:
                current.append(line)
            continue
        current.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt and not stmt.startswith("--"):
                statements.append(stmt)
            current = []

    # Dodaj ostatnią instrukcję jeśli nie kończyła się ;
    if current:
        stmt = "\n".join(current).strip()
        if stmt and not stmt.startswith("--"):
            statements.append(stmt)

    print(f"\n[{label}] {len(statements)} instrukcji do wykonania...")
    cur = conn.cursor()
    ok = 0
    for i, stmt in enumerate(statements, 1):
        try:
            cur.execute(stmt)
            ok += 1
            if i % 50 == 0:
                print(f"  ... {i}/{len(statements)}")
        except Exception as e:
            print(f"  [!] Błąd przy instrukcji {i}: {e}")
            print(f"      SQL: {stmt[:120]}...")
            conn.rollback()
            # Kontynuuj – nie przerywaj całości
            cur = conn.cursor()
    conn.commit()
    cur.close()
    print(f"[{label}] Gotowe: {ok}/{len(statements)} OK")

def main():
    print(f"Łączenie z: {DB_URL[:60]}...")
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=15, sslmode="require")
    except Exception as e:
        print(f"\n[BŁĄD] Nie można połączyć się z bazą:\n  {e}")
        print("\nUpewnij się że:")
        print("  1. Projekt Supabase jest aktywny")
        print("  2. Hasło i project_ref są poprawne")
        print("  3. Firewall/sieć pozwala na port 5432")
        print("\nAlternatywnie podaj DATABASE_URL jako zmienną środowiskową:")
        print("  DATABASE_URL=postgresql://... python apply_migration.py")
        sys.exit(1)

    print("Połączono!")

    # Sprawdź czy tabele już istnieją
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('surowce','produkty','skladniki_produktu')")
    existing = [r[0] for r in cur.fetchall()]
    cur.close()
    if existing:
        print(f"Istniejące tabele: {existing}")
    else:
        print("Brak tabel – świeża baza.")

    run_sql_file(conn, SCHEMA_FILE, "SCHEMA")
    run_sql_file(conn, DATA_FILE, "DATA")

    # Weryfikacja
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM surowce")
    n_s = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM produkty")
    n_p = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM skladniki_produktu")
    n_sk = cur.fetchone()[0]
    cur.close()
    conn.close()

    print(f"\n=== Weryfikacja ===")
    print(f"  surowce:            {n_s} wierszy")
    print(f"  produkty:           {n_p} wierszy")
    print(f"  skladniki_produktu: {n_sk} wierszy")
    print("\n[OK] Migracja zakończona!")

if __name__ == "__main__":
    main()
