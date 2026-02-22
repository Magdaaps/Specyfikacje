import sqlite3
import os

# Check both possible locations
locations = [
    os.path.join(os.getcwd(), "product_generator.db"),
    os.path.join(os.path.dirname(os.getcwd()), "product_generator.db"),
    "product_generator.db"
]

# Specifically check the one defined in database.py's logic
backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(backend_dir)
locations.append(os.path.join(root_dir, "product_generator.db"))
locations.append(os.path.join(backend_dir, "product_generator.db"))

print(f"Checking locations for database...")

for db_path in set(locations):
    if os.path.exists(db_path):
        print(f"\n>>> Found database at: {db_path}")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # List of columns to add
            columns_to_add = [
                ("organoleptyka_smak", "TEXT"),
                ("organoleptyka_zapach", "TEXT"),
                ("organoleptyka_kolor", "TEXT"),
                ("organoleptyka_wyglad_zewnetrzny", "TEXT"),
                ("organoleptyka_wyglad_na_przekroju", "TEXT")
            ]

            for col_name, col_type in columns_to_add:
                try:
                    cursor.execute(f"ALTER TABLE produkty ADD COLUMN {col_name} {col_type}")
                    print(f"  + Column {col_name} added.")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print(f"  - Column {col_name} already exists.")
                    else:
                        print(f"  ! Error adding {col_name}: {e}")

            conn.commit()
            conn.close()
            print(f">>> Migration finished for {db_path}")
        except Exception as e:
            print(f">>> ERROR migrating {db_path}: {e}")

print("\nAll found databases have been checked/migrated.")
