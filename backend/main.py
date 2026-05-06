import json
import logging
import re
import time
import unicodedata
from fastapi import FastAPI, Depends, HTTPException, Query, Request, Response, File, UploadFile, Body
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, crud, logic, excel_gen, pdf_gen, sharepoint, exceptions
from database import engine, get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger("generator-api")

models.Base.metadata.create_all(bind=engine)

# Migracje kolumn dodanych po pierwszym create_all
def _run_migrations():
    with engine.connect() as conn:
        from sqlalchemy import text as sa_text
        for col in ("sklad_text", "origins_override"):
            try:
                conn.execute(sa_text(f"ALTER TABLE produkty ADD COLUMN IF NOT EXISTS {col} TEXT"))
                conn.commit()
            except Exception:
                try:
                    conn.execute(sa_text(f"ALTER TABLE produkty ADD COLUMN {col} TEXT"))
                    conn.commit()
                except Exception:
                    pass  # Kolumna już istnieje

_run_migrations()

app = FastAPI(title="Generator Kart Produktów 2.0 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# Create uploads directory if not exists
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"path={request.url.path} method={request.method} completed_in={formatted_process_time}ms status_code={response.status_code}")
    return response

@app.exception_handler(exceptions.AppError)
async def app_error_handler(request: Request, exc: exceptions.AppError):
    logger.error(f"AppError: {exc.message} - Details: {exc.details}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "An internal server error occurred.", "details": str(exc)},
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to Product Card Generator API"}

# --- SUROWCE ---
@app.get("/surowce", response_model=List[schemas.Surowiec])
def read_surowce(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_surowce(db, skip=skip, limit=limit)
    logger.info(f"DB: Fetched {len(items)} raw materials (surowce)")
    return items

@app.post("/surowce", response_model=schemas.Surowiec)
def create_surowiec(surowiec: schemas.SurowiecCreate, db: Session = Depends(get_db)):
    logger.info(f"DB: Creating new material: {surowiec.nazwa}")
    return crud.create_surowiec(db=db, surowiec=surowiec)

@app.get("/surowce/{surowiec_id}", response_model=schemas.Surowiec)
def read_surowiec(surowiec_id: int, db: Session = Depends(get_db)):
    db_surowiec = crud.get_surowiec(db, surowiec_id=surowiec_id)
    if db_surowiec is None:
        raise HTTPException(status_code=404, detail="Surowiec not found")
    return db_surowiec

@app.put("/surowce/{surowiec_id}", response_model=schemas.Surowiec)
def update_surowiec(surowiec_id: int, surowiec: schemas.SurowiecCreate, db: Session = Depends(get_db)):
    return crud.update_surowiec(db=db, surowiec_id=surowiec_id, surowiec=surowiec)

@app.delete("/surowce/{surowiec_id}")
def delete_surowiec(surowiec_id: int, db: Session = Depends(get_db)):
    db_surowiec = crud.delete_surowiec(db=db, surowiec_id=surowiec_id)
    if db_surowiec is None:
        raise HTTPException(status_code=404, detail="Surowiec not found")
    logger.info(f"DB: Deleted surowiec id={surowiec_id}")
    return {"ok": True}

# --- PRODUKTY ---
# Sentinel for products with empty-string EAN (primary key = "").
# Frontend passes "~" when item.ean is empty; backend decodes it back to "".
_EAN_EMPTY_SENTINEL = "~"

def _decode_ean(ean: str) -> str:
    from urllib.parse import unquote
    ean = unquote(ean)
    return "" if ean == _EAN_EMPTY_SENTINEL else ean

@app.get("/produkty", response_model=List[schemas.Produkt])
def read_produkty(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_produkty(db, skip=skip, limit=limit)
    return items

@app.put("/produkty/{ean}", response_model=schemas.Produkt)
def update_produkt(ean: str, produkt: schemas.ProduktCreate, db: Session = Depends(get_db)):
    ean = _decode_ean(ean)
    logger.info(f"DB: UPDATING PRODUCT (PUT) EAN: {ean!r}")
    db_produkt = crud.update_produkt(db=db, ean=ean, produkt=produkt)
    if db_produkt is None:
        raise HTTPException(status_code=404, detail="Produkt not found")
    return db_produkt

@app.patch("/produkty/{ean}/image")
def update_product_image(ean: str, image_url: Optional[str] = Body(None, embed=True), db: Session = Depends(get_db)):
    db_produkt = crud.get_produkt(db, ean=ean)
    if db_produkt is None:
        raise HTTPException(status_code=404, detail="Produkt not found")
    db_produkt.image_url = image_url
    db.commit()
    logger.info(f"Image URL updated for EAN {ean}: {image_url}")
    return {"image_url": db_produkt.image_url}

@app.get("/produkty/sugestie/organoleptyka")
def get_organoleptyka_suggestions(
    field: str, 
    q: str = "", 
    recent: bool = False,
    current_ean: Optional[str] = None,
    db: Session = Depends(get_db)
):
    allowed_fields = [
        "organoleptyka_smak", 
        "organoleptyka_zapach", 
        "organoleptyka_kolor", 
        "organoleptyka_wyglad_zewnetrzny", 
        "organoleptyka_wyglad_na_przekroju",
        "warunki_przechowywania",
        "termin_przydatnosci",
        "wyrazenie_format_daty",
        "informacje_dodatkowe",
        "prawna_nazwa_pl",
        "prawna_nazwa_en",
        "kod_cn",
        "kod_pkwiu",
        "logistyka_rodzaj_palety"
    ]
    
    if field == "certyfikat_rodzaj":
        # Special handling for values inside JSON field 'certyfikaty'
        from sqlalchemy import select
        import json
        query = select(models.Produkt.certyfikaty).where(models.Produkt.certyfikaty.isnot(None))
        if current_ean:
            query = query.where(models.Produkt.ean != current_ean)
        
        results = db.execute(query).scalars().all()
        
        all_rodzaje = set()
        for c_str in results:
            try:
                c_list = json.loads(c_str)
                for c in c_list:
                    rodzaj = c.get("rodzaj", "")
                    if rodzaj and q.lower() in rodzaj.lower():
                        all_rodzaje.add(rodzaj)
            except:
                continue
        
        return sorted(list(all_rodzaje))[:10]

    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"Invalid field: {field}")
    
    # Get unique values for the field that match the query
    from sqlalchemy import select, desc
    column = getattr(models.Produkt, field)
    
    query = select(column).where(column.isnot(None)).where(column != "")
    
    if q:
        query = query.where(column.ilike(f"%{q}%"))
        
    if current_ean:
        query = query.where(models.Produkt.ean != current_ean)
        
    if recent:
        # Sort by updated_at to get truly recent ones
        query = query.order_by(desc(models.Produkt.updated_at))
        # We need to get unique values but keep the order of newest products
        results = db.execute(query.limit(50)).scalars().all()
        unique_results = []
        for r in results:
            if r and r not in unique_results:
                unique_results.append(r)
            if len(unique_results) >= 10:
                break
        return unique_results
    else:
        results = db.execute(query.distinct().limit(10)).scalars().all()
        return [r for r in results if r]

@app.get("/produkty/{ean}", response_model=schemas.Produkt)
def read_produkt(ean: str, db: Session = Depends(get_db)):
    ean = _decode_ean(ean)
    db_produkt = crud.get_produkt(db, ean=ean)
    if db_produkt is None:
        raise HTTPException(status_code=404, detail="Produkt not found")
    return db_produkt

@app.delete("/produkty/{ean}")
def delete_produkt(ean: str, db: Session = Depends(get_db)):
    ean = _decode_ean(ean)
    db_produkt = crud.delete_produkt(db=db, ean=ean)
    if db_produkt is None:
        raise HTTPException(status_code=404, detail="Produkt not found")
    logger.info(f"DB: Deleted produkt EAN={ean}")
    return {"ok": True}

@app.post("/produkty", response_model=schemas.Produkt)
def create_produkt(produkt: schemas.ProduktCreate, db: Session = Depends(get_db)):
    # Check if exists
    db_existing = crud.get_produkt(db, ean=produkt.ean)
    if db_existing:
        raise HTTPException(status_code=400, detail="EAN already registered")
    return crud.create_produkt(db=db, produkt=produkt)


# Business Logic Endpoints
@app.get("/produkty/{ean}/analiza")
def analyze_product(ean: str, db: Session = Depends(get_db)):
    ean = _decode_ean(ean)
    logger.info(f"Analyzing product with EAN: {ean!r}")
    db_produkt = crud.get_produkt(db, ean=ean)
    if not db_produkt:
        raise exceptions.DataNotFoundError(f"Produkt with EAN {ean} not found")
    
    try:
        nutrition = logic.calculate_nutrition(db_produkt)
        allergens = logic.aggregate_allergens(db_produkt)
        sklad_pl = logic.generate_ingredients_text(db_produkt, lang="pl")
        sklad_en = logic.generate_ingredients_text(db_produkt, lang="en")
        if db_produkt.origins_override:
            try:
                ingredient_origins = json.loads(db_produkt.origins_override)
            except Exception:
                ingredient_origins = logic.get_ingredient_origins(db_produkt)
        else:
            ingredient_origins = logic.get_ingredient_origins(db_produkt)

        return {
            "ean": ean,
            "nutrition": nutrition,
            "allergens": allergens,
            "ingredients_pl": sklad_pl,
            "ingredients_en": sklad_en,
            "ingredient_origins": ingredient_origins
        }
    except Exception as e:
        logger.error(f"Analysis failed for EAN {ean}: {e}")
        raise exceptions.AppError(f"Failed to analyze product: {str(e)}")

@app.get("/produkty/{ean}/download")
def download_card(ean: str, lang: str = "pl", db: Session = Depends(get_db)):
    ean = _decode_ean(ean)
    logger.info(f"Generating download for EAN: {ean!r}, lang: {lang}")
    db_produkt = crud.get_produkt(db, ean=ean)
    if not db_produkt:
        raise exceptions.DataNotFoundError(f"Produkt with EAN {ean} not found")
    
    try:
        output = excel_gen.generate_product_card(db_produkt, lang=lang)
        
        filename = f"Karta_Produktu_{ean}_{lang}.xlsx"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return Response(
            content=output.getvalue(), 
            headers=headers, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        logger.error(f"Download generation failed for EAN {ean}: {e}")
        raise exceptions.AppError(f"Failed to generate Excel file: {str(e)}")

@app.post("/produkty/{ean}/sharepoint")
def sync_to_sharepoint(ean: str, folder: str, lang: str = "pl", db: Session = Depends(get_db)):
    logger.info(f"Syncing EAN {ean} to SharePoint folder: {folder}")
    db_produkt = crud.get_produkt(db, ean=ean)
    if not db_produkt:
        raise exceptions.DataNotFoundError(f"Produkt with EAN {ean} not found")
    
    try:
        output = excel_gen.generate_product_card(db_produkt, lang=lang)
        filename = f"Karta_Produktu_{ean}_{lang}.xlsx"
        
        success = sharepoint.upload_to_sharepoint(output.getvalue(), folder, filename)
        if not success:
            raise exceptions.SharePointError("SharePoint upload failed")
        
        return {"message": "Successfully uploaded to SharePoint", "filename": filename}
    except exceptions.AppError:
        raise
    except Exception as e:
        logger.error(f"SharePoint sync failed for EAN {ean}: {e}")
        raise exceptions.SharePointError(f"Failed to sync with SharePoint: {str(e)}")

@app.patch("/produkty/{ean}/sklad_text")
def update_sklad_text(ean: str, body: dict = Body(...), db: Session = Depends(get_db)):
    ean = _decode_ean(ean)
    db_produkt = crud.get_produkt(db, ean=ean)
    if not db_produkt:
        raise exceptions.DataNotFoundError(f"Produkt with EAN {ean} not found")
    db_produkt.sklad_text = body.get("sklad_text") or None
    db.commit()
    return {"ok": True}

@app.patch("/produkty/{ean}/origins_override")
def update_origins_override(ean: str, body: dict = Body(...), db: Session = Depends(get_db)):
    ean = _decode_ean(ean)
    db_produkt = crud.get_produkt(db, ean=ean)
    if not db_produkt:
        raise exceptions.DataNotFoundError(f"Produkt with EAN {ean} not found")
    db_produkt.origins_override = body.get("origins_override") or None
    db.commit()
    return {"ok": True}

@app.get("/produkty/{ean}/pdf")
def download_pdf(ean: str, lang: str = "pl", db: Session = Depends(get_db)):
    ean = _decode_ean(ean)
    logger.info(f"Generating PDF for EAN: {ean!r}, lang: {lang}")
    db_produkt = crud.get_produkt(db, ean=ean)
    if not db_produkt:
        raise exceptions.DataNotFoundError(f"Produkt with EAN {ean} not found")

    try:
        output = pdf_gen.generate_pdf(db_produkt, lang=lang)

        lang_suffix = f"_{lang.upper()}" if lang != "pl" else ""
        filename = f"Specyfikacja_{ean}{lang_suffix}.pdf"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return Response(
            content=output.getvalue(),
            headers=headers,
            media_type="application/pdf"
        )
    except Exception as e:
        logger.exception(f"PDF generation failed for EAN {ean}: {e}")
        raise exceptions.AppError(f"Failed to generate PDF file: {str(e)}")

# --- UPLOAD ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
SUPABASE_BUCKET = "product-images"

def _sanitize_filename(filename: str) -> str:
    """Sanitize filename for Supabase Storage: remove non-ASCII, spaces, duplicate extensions."""
    # Extract the last (real) extension
    name, ext = os.path.splitext(filename)
    # If the stem still has extensions (e.g. "foo.jpg2.jpg3" → stem="foo.jpg2", ext=".jpg3"),
    # strip all intermediate extensions from the stem too
    while True:
        stem, mid_ext = os.path.splitext(name)
        if mid_ext:
            name = stem
        else:
            break
    # Normalize unicode (ą→a, ł→l, etc.)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    # Replace spaces and unsafe chars with underscores
    name = re.sub(r"[^\w.-]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        name = "image"
    return name + ext.lower()


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    content = await file.read()
    safe_filename = _sanitize_filename(file.filename or "image.jpg")

    if SUPABASE_URL and SUPABASE_SERVICE_KEY:
        import httpx
        storage_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{safe_filename}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    storage_url,
                    content=content,
                    headers={
                        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                        "Content-Type": file.content_type or "application/octet-stream",
                        "x-upsert": "true",
                    },
                )
        except httpx.TimeoutException:
            logger.error("Supabase Storage upload timed out")
            raise HTTPException(status_code=500, detail="Przekroczono czas połączenia z Supabase Storage")
        except httpx.RequestError as e:
            logger.error(f"Supabase Storage connection error: {e}")
            raise HTTPException(status_code=500, detail=f"Błąd połączenia z Supabase Storage: {e}")
        if resp.status_code not in (200, 201):
            logger.error(f"Supabase Storage upload failed: {resp.status_code} {resp.text}")
            raise HTTPException(status_code=500, detail=f"Supabase Storage odmówił uploadu ({resp.status_code}): {resp.text[:200]}")
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{safe_filename}"
        logger.info(f"Image uploaded to Supabase Storage: {public_url}")
        return {"url": public_url}
    else:
        # Fallback: local filesystem (development)
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        return {"url": f"/uploads/{safe_filename}"}
