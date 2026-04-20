"""
Migruje obrazki ze starego Supabase (epriyloxnspwhoumpewj) do nowego (ggltivnjuwtoahqyfcwa)
i aktualizuje URL-e w Neon.
"""
import os
import httpx
from sqlalchemy import create_engine, text

NEON_URL = os.getenv("DATABASE_URL", "")
OLD_BASE  = "https://epriyloxnspwhoumpewj.supabase.co/storage/v1/object/public/product-images"
NEW_BASE  = "https://ggltivnjuwtoahqyfcwa.supabase.co"
NEW_KEY   = os.getenv("SUPABASE_SERVICE_KEY", "")
BUCKET    = "product-images"

engine = create_engine(NEON_URL, pool_pre_ping=True)

with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT ean, image_url FROM produkty WHERE image_url LIKE '%epriyloxnspwhoumpewj%'"
    )).fetchall()

print(f"Produktów do migracji: {len(rows)}\n")

headers_new = {
    "Authorization": f"Bearer {NEW_KEY}",
    "apikey": NEW_KEY,
}

migrated = 0
for ean, old_url in rows:
    filename = old_url.split("/")[-1]
    ext = filename.rsplit(".", 1)[-1].lower()
    content_type = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"

    # Pobierz ze starego
    r = httpx.get(f"{OLD_BASE}/{filename}", timeout=30)
    if r.status_code != 200:
        print(f"[!] {ean} – brak pliku: {filename} ({r.status_code})")
        continue

    # Wgraj do nowego
    upload = httpx.post(
        f"{NEW_BASE}/storage/v1/object/{BUCKET}/{filename}",
        content=r.content,
        headers={**headers_new, "Content-Type": content_type, "x-upsert": "true"},
        timeout=30,
    )
    if upload.status_code not in (200, 201):
        print(f"[!] {ean} – upload failed: {upload.status_code} {upload.text[:80]}")
        continue

    new_url = f"{NEW_BASE}/storage/v1/object/public/{BUCKET}/{filename}"

    # Zaktualizuj Neon
    with engine.connect() as conn:
        conn.execute(text("UPDATE produkty SET image_url = :url WHERE ean = :ean"),
                     {"url": new_url, "ean": ean})
        conn.commit()

    print(f"[OK] {ean}: {filename}")
    migrated += 1

print(f"\nMigracja: {migrated}/{len(rows)} obrazków.")
