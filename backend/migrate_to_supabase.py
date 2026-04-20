"""
Skrypt migracyjny: lokalny SQLite -> Supabase

Co robi:
1. Uploaduje obrazki do Supabase Storage (przez REST API)
2. Generuje supabase_schema.sql - wklej w SQL Editor Supabase
3. Generuje supabase_data.sql  - wklej w SQL Editor Supabase po schema

Uruchomienie:
    cd backend
    venv/Scripts/python migrate_to_supabase.py
"""
import io, os, sys, glob, sqlite3, json, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import httpx

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ggltivnjuwtoahqyfcwa.supabase.co")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
SUPABASE_BUCKET = "product-images"

HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
}

# -- Znajdz lokalna baze SQLite -----------------------------------------------

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sqlite_path = os.path.join(project_root, "product_generator.db")
uploads_dir = os.path.join(script_dir, "uploads")

if not os.path.exists(sqlite_path):
    matches = glob.glob(os.path.join(project_root, "*.db"))
    sqlite_path = matches[0] if matches else None

print(f"SQLite: {sqlite_path}")
print(f"Uploads: {uploads_dir}")
print()

# -- Wczytaj dane -------------------------------------------------------------

conn = sqlite3.connect(sqlite_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT * FROM surowce")
surowce = [dict(r) for r in cur.fetchall()]
cur.execute("SELECT * FROM produkty")
produkty = [dict(r) for r in cur.fetchall()]
cur.execute("SELECT * FROM skladniki_produktu")
skladniki = [dict(r) for r in cur.fetchall()]
conn.close()
print(f"Wczytano: {len(surowce)} surowcow, {len(produkty)} produktow, {len(skladniki)} skladnikow")
print()

# -- KROK 1: Stworz bucket w Supabase Storage ---------------------------------

print("=== KROK 1: Supabase Storage ===")
resp = httpx.get(f"{SUPABASE_URL}/storage/v1/bucket/{SUPABASE_BUCKET}", headers=HEADERS)
if resp.status_code == 200:
    print(f"  Bucket '{SUPABASE_BUCKET}' juz istnieje.")
else:
    resp = httpx.post(
        f"{SUPABASE_URL}/storage/v1/bucket",
        headers={**HEADERS, "Content-Type": "application/json"},
        content=json.dumps({"id": SUPABASE_BUCKET, "name": SUPABASE_BUCKET, "public": True}).encode()
    )
    if resp.status_code in (200, 201):
        print(f"  [OK] Bucket '{SUPABASE_BUCKET}' utworzony (publiczny).")
    else:
        print(f"  [!] Blad tworzenia bucketu: {resp.status_code} {resp.text[:200]}")
print()

# -- KROK 2: Uploaduj obrazki -------------------------------------------------

print("=== KROK 2: Upload obrazkow ===")
image_url_map = {}

for p in produkty:
    url = p.get("image_url")
    if not url or not url.startswith("/uploads/"):
        continue
    filename = url.split("/uploads/")[-1]
    local_path = os.path.join(uploads_dir, filename)
    if not os.path.exists(local_path):
        print(f"  [!] Brak pliku lokalnie: {local_path}")
        continue
    ext = os.path.splitext(filename)[1].lower()
    content_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
    with open(local_path, "rb") as f:
        content = f.read()
    resp = httpx.post(
        f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}",
        content=content,
        headers={**HEADERS, "Content-Type": content_type, "x-upsert": "true"},
    )
    if resp.status_code in (200, 201):
        new_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
        image_url_map[url] = new_url
        print(f"  [OK] {filename}")
    else:
        print(f"  [X] {filename}: {resp.status_code} {resp.text[:150]}")

print()

# -- KROK 3: Generuj SQL schema -----------------------------------------------

print("=== KROK 3: Generowanie SQL ===")

def sql_val(v):
    """Konwertuje wartosc Pythona na SQL literal."""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    # String - escape single quotes
    escaped = str(v).replace("'", "''")
    return f"'{escaped}'"

schema_sql = """\
-- ============================================================
-- Supabase Schema - Generator Kart Produktow
-- Wklej w: Supabase Dashboard > SQL Editor > New query
-- ============================================================

-- SUROWCE
CREATE TABLE IF NOT EXISTS surowce (
    id SERIAL PRIMARY KEY,
    nazwa TEXT UNIQUE,
    nazwa_en TEXT,
    kraj_pochodzenia TEXT,
    energia_kj FLOAT DEFAULT 0.0,
    energia_kcal FLOAT DEFAULT 0.0,
    tluszcz FLOAT DEFAULT 0.0,
    kwasy_nasycone FLOAT DEFAULT 0.0,
    weglowodany FLOAT DEFAULT 0.0,
    cukry FLOAT DEFAULT 0.0,
    bialko FLOAT DEFAULT 0.0,
    sol FLOAT DEFAULT 0.0,
    blonnik FLOAT DEFAULT 0.0,
    alergen_gluten TEXT DEFAULT 'Nie zawiera',
    alergen_skorupiaki TEXT DEFAULT 'Nie zawiera',
    alergen_jaja TEXT DEFAULT 'Nie zawiera',
    alergen_ryby TEXT DEFAULT 'Nie zawiera',
    alergen_orzeszki_ziemne TEXT DEFAULT 'Nie zawiera',
    alergen_soja TEXT DEFAULT 'Nie zawiera',
    alergen_mleko TEXT DEFAULT 'Nie zawiera',
    alergen_orzechy TEXT DEFAULT 'Nie zawiera',
    alergen_seler TEXT DEFAULT 'Nie zawiera',
    alergen_gorczyca TEXT DEFAULT 'Nie zawiera',
    alergen_sezam TEXT DEFAULT 'Nie zawiera',
    alergen_dwutlenek_siarki TEXT DEFAULT 'Nie zawiera',
    alergen_lubin TEXT DEFAULT 'Nie zawiera',
    alergen_mieczaki TEXT DEFAULT 'Nie zawiera',
    sklad_pl TEXT,
    sklad_en TEXT,
    sklad_procentowy TEXT,
    pochodzenie_skladnikow TEXT,
    kategoria TEXT DEFAULT 'Inne'
);

-- PRODUKTY
CREATE TABLE IF NOT EXISTS produkty (
    ean VARCHAR(13) PRIMARY KEY,
    internal_id VARCHAR(6),
    nazwa_pl TEXT,
    nazwa_en TEXT,
    prawna_nazwa_pl TEXT,
    prawna_nazwa_en TEXT,
    ean_karton VARCHAR(13),
    kategoria TEXT,
    masa_netto TEXT,
    image_url TEXT,
    product_type TEXT DEFAULT 'inne',
    organoleptyka_smak TEXT,
    organoleptyka_zapach TEXT,
    organoleptyka_kolor TEXT,
    organoleptyka_wyglad_zewnetrzny TEXT,
    organoleptyka_wyglad_na_przekroju TEXT,
    warunki_przechowywania TEXT,
    termin_przydatnosci TEXT,
    wyrazenie_format_daty TEXT,
    informacje_dodatkowe TEXT,
    alergeny TEXT,
    kod_cn TEXT,
    kod_pkwiu TEXT,
    certyfikaty TEXT,
    logistyka_wymiary_solo_h FLOAT DEFAULT 0.0,
    logistyka_wymiary_solo_w FLOAT DEFAULT 0.0,
    logistyka_wymiary_solo_d FLOAT DEFAULT 0.0,
    logistyka_wymiary_jednostka_h FLOAT DEFAULT 0.0,
    logistyka_wymiary_jednostka_w FLOAT DEFAULT 0.0,
    logistyka_wymiary_jednostka_d FLOAT DEFAULT 0.0,
    logistyka_wymiary_zbiorcze1_h FLOAT DEFAULT 0.0,
    logistyka_wymiary_zbiorcze1_w FLOAT DEFAULT 0.0,
    logistyka_wymiary_zbiorcze1_d FLOAT DEFAULT 0.0,
    logistyka_wymiary_zbiorcze2_h FLOAT DEFAULT 0.0,
    logistyka_wymiary_zbiorcze2_w FLOAT DEFAULT 0.0,
    logistyka_wymiary_zbiorcze2_d FLOAT DEFAULT 0.0,
    logistyka_wymiary_zbiorcze3_h FLOAT DEFAULT 0.0,
    logistyka_wymiary_zbiorcze3_w FLOAT DEFAULT 0.0,
    logistyka_wymiary_zbiorcze3_d FLOAT DEFAULT 0.0,
    logistyka_rodzaj_palety TEXT,
    logistyka_waga_netto_szt FLOAT DEFAULT 0.0,
    logistyka_waga_brutto_szt FLOAT DEFAULT 0.0,
    logistyka_waga_netto_zbiorcze FLOAT DEFAULT 0.0,
    logistyka_waga_brutto_zbiorcze FLOAT DEFAULT 0.0,
    logistyka_waga_netto_paleta FLOAT DEFAULT 0.0,
    logistyka_waga_brutto_paleta FLOAT DEFAULT 0.0,
    logistyka_sztuk_w_zbiorczym INTEGER DEFAULT 0,
    logistyka_kartonow_na_warstwie INTEGER DEFAULT 0,
    logistyka_warstw_na_palecie INTEGER DEFAULT 0,
    logistyka_kartonow_na_palecie INTEGER DEFAULT 0,
    logistyka_sztuk_na_palecie INTEGER DEFAULT 0,
    logistyka_sztuk_na_warstwie INTEGER DEFAULT 0,
    logistyka_wysokosc_palety FLOAT DEFAULT 0.0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- SKLADNIKI_PRODUKTU
CREATE TABLE IF NOT EXISTS skladniki_produktu (
    id SERIAL PRIMARY KEY,
    produkt_ean VARCHAR(13) REFERENCES produkty(ean) ON DELETE CASCADE,
    surowiec_id INTEGER REFERENCES surowce(id),
    procent FLOAT,
    kolejnosc INTEGER
);

-- SLOWNIK
CREATE TABLE IF NOT EXISTS slownik (
    id SERIAL PRIMARY KEY,
    kategoria TEXT,
    pl TEXT,
    en TEXT
);
"""

schema_path = os.path.join(script_dir, "supabase_schema.sql")
with open(schema_path, "w", encoding="utf-8") as f:
    f.write(schema_sql)
print(f"  [OK] Zapisano: supabase_schema.sql")

# -- KROK 4: Generuj SQL z danymi ---------------------------------------------

lines = ["-- ============================================================"]
lines.append("-- Supabase Data - Generator Kart Produktow")
lines.append("-- Uruchom PO supabase_schema.sql")
lines.append("-- ============================================================")
lines.append("")

# Surowce
lines.append("-- SUROWCE")
cols_s = list(surowce[0].keys()) if surowce else []
for s in surowce:
    col_str = ", ".join(cols_s)
    val_str = ", ".join(sql_val(s[c]) for c in cols_s)
    update_str = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols_s if c != "id")
    lines.append(f"INSERT INTO surowce ({col_str}) VALUES ({val_str})")
    lines.append(f"  ON CONFLICT (id) DO UPDATE SET {update_str};")
lines.append("")
lines.append(f"SELECT setval('surowce_id_seq', (SELECT MAX(id) FROM surowce));")
lines.append("")

# Produkty
lines.append("-- PRODUKTY")
cols_p = list(produkty[0].keys()) if produkty else []
# Remove updated_at - let DB handle it
cols_p_filtered = [c for c in cols_p if c != "updated_at"]
for p in produkty:
    # Update image_url to Supabase URL if migrated
    if p.get("image_url") in image_url_map:
        p = dict(p)
        p["image_url"] = image_url_map[p["image_url"]]
    col_str = ", ".join(cols_p_filtered)
    val_str = ", ".join(sql_val(p[c]) for c in cols_p_filtered)
    update_str = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols_p_filtered if c != "ean")
    lines.append(f"INSERT INTO produkty ({col_str}) VALUES ({val_str})")
    lines.append(f"  ON CONFLICT (ean) DO UPDATE SET {update_str};")
lines.append("")

# Skladniki
lines.append("-- SKLADNIKI_PRODUKTU")
cols_sk = list(skladniki[0].keys()) if skladniki else []
for s in skladniki:
    col_str = ", ".join(cols_sk)
    val_str = ", ".join(sql_val(s[c]) for c in cols_sk)
    update_str = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols_sk if c != "id")
    lines.append(f"INSERT INTO skladniki_produktu ({col_str}) VALUES ({val_str})")
    lines.append(f"  ON CONFLICT (id) DO UPDATE SET {update_str};")
lines.append("")
lines.append(f"SELECT setval('skladniki_produktu_id_seq', (SELECT MAX(id) FROM skladniki_produktu));")

data_path = os.path.join(script_dir, "supabase_data.sql")
with open(data_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"  [OK] Zapisano: supabase_data.sql ({len(lines)} linii)")
print()

# -- Podsumowanie -------------------------------------------------------------

print("=" * 60)
print("[OK] Gotowe!")
print()
print("NASTEPNE KROKI:")
print()
print("1. Otworz Supabase SQL Editor:")
print("   https://supabase.com/dashboard/project/ggltivnjuwtoahqyfcwa/sql/new")
print()
print("2. Skopiuj zawartosc 'supabase_schema.sql' i uruchom")
print()
print("3. Skopiuj zawartosc 'supabase_data.sql' i uruchom")
print()
if image_url_map:
    print(f"4. Obrazki ({len(image_url_map)}) zostaly wgrane do Supabase Storage:")
    for old, new in image_url_map.items():
        print(f"   {old} -> {new.split('/')[-1]}")
else:
    print("   Brak obrazkow do migracji przez Storage API.")
print()
print("5. Ustaw w Render Dashboard:")
print(f"   DATABASE_URL = postgresql://postgres.ggltivnjuwtoahqyfcwa:rFH8nIFuFGVopXud@[POOLER_HOST]:5432/postgres")
print(f"   SUPABASE_URL = {SUPABASE_URL}")
print(f"   SUPABASE_SERVICE_KEY = {SUPABASE_SERVICE_KEY}")
