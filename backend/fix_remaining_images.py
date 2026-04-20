import io, os, sys, httpx
from urllib.parse import quote
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from sqlalchemy import create_engine, text

NEON = os.getenv("DATABASE_URL", "")
OLD_BASE = 'https://epriyloxnspwhoumpewj.supabase.co/storage/v1/object/public/product-images'
NEW_BASE = 'https://ggltivnjuwtoahqyfcwa.supabase.co'
NEW_KEY  = os.getenv("SUPABASE_SERVICE_KEY", "")
BUCKET   = 'product-images'
headers  = {'Authorization': f'Bearer {NEW_KEY}', 'apikey': NEW_KEY}
engine   = create_engine(NEON, pool_pre_ping=True)

to_migrate = [
    ('5907244100518', '10. Lizak z białej_mlecznej czekolady 15g strzelający Halloween flow pack.jpg'),
    ('123456789',     'Obraz13.png'),
]

for ean, filename in to_migrate:
    encoded = quote(filename, safe='')
    r = httpx.get(f'{OLD_BASE}/{encoded}', timeout=30)
    print(f'{ean} | {filename[:50]} -> {r.status_code}')
    if r.status_code != 200:
        print(f'  SKIP (brak pliku w starym Supabase)')
        continue
    ext = filename.rsplit('.', 1)[-1].lower()
    ct  = 'image/jpeg' if ext in ('jpg', 'jpeg') else 'image/png'
    up  = httpx.post(
        f'{NEW_BASE}/storage/v1/object/{BUCKET}/{encoded}',
        content=r.content, timeout=30,
        headers={**headers, 'Content-Type': ct, 'x-upsert': 'true'}
    )
    print(f'  upload: {up.status_code}')
    if up.status_code in (200, 201):
        new_url = f'{NEW_BASE}/storage/v1/object/public/{BUCKET}/{encoded}'
        with engine.connect() as conn:
            conn.execute(text('UPDATE produkty SET image_url=:u WHERE ean=:e'), {'u': new_url, 'e': ean})
            conn.commit()
        print(f'  OK: Neon zaktualizowany')
