import csv
import os
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend import models

# Ensure tables are created
models.Base.metadata.create_all(bind=engine)

def normalize_allergen(status):
    if not status:
        return "Nie zawiera"
    s = str(status).lower().strip()
    if "zawiera" in s and "może" not in s and "moze" not in s:
        return "Zawiera"
    if "może" in s or "moze" in s or "śladowe" in s or "ślad" in s:
        return "Może zawierać"
    return "Nie zawiera"

def seed():
    db = SessionLocal()
    try:
        # 1. Seed Surowce
        print("Seeding surowce...")
        seen_names = set()
        with open('data/Surowce.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('Nazwa surowca')
                if not name or name.strip() == "" or name in seen_names:
                    continue
                seen_names.add(name)
                
                surowiec = models.Surowiec(
                    nazwa=name,
                    energia_kj=float(row.get('Energia [kJ/100g]', 0) or 0),
                    energia_kcal=float(row.get('Energia [kcal/100g]', 0) or 0),
                    tluszcz=float(row.get('Tłuszcz [g]', 0) or 0),
                    kwasy_nasycone=float(row.get('Kwasy tłuszczowe nasycone [g]', 0) or 0),
                    weglowodany=float(row.get('Węglowodany [g]', 0) or 0),
                    cukry=float(row.get('Cukry [g]', 0) or 0),
                    bialko=float(row.get('Białko [g]', 0) or 0),
                    sol=float(row.get('Sól [g]', 0) or 0),
                    kraj_pochodzenia=row.get('Cukier.1', ''),
                    
                    alergen_gluten=normalize_allergen(row.get('Gluten')),
                    alergen_skorupiaki=normalize_allergen(row.get('Skorupiaki')),
                    alergen_jaja=normalize_allergen(row.get('Jaja')),
                    alergen_ryby=normalize_allergen(row.get('Ryby')),
                    alergen_orzeszki_ziemne=normalize_allergen(row.get('Orzeszki ziemne')),
                    alergen_soja=normalize_allergen(row.get('Soja')),
                    alergen_mleko=normalize_allergen(row.get('Mleko')),
                    alergen_orzechy=normalize_allergen(row.get('Orzechy')),
                    alergen_seler=normalize_allergen(row.get('Seler')),
                    alergen_gorczyca=normalize_allergen(row.get('Gorczyca')),
                    alergen_sezam=normalize_allergen(row.get('Sezam')),
                    alergen_dwutlenek_siarki=normalize_allergen(row.get('Dwutlenek siarki i siarczyny')),
                    alergen_lubin=normalize_allergen(row.get('Łubin')),
                    alergen_mieczaki=normalize_allergen(row.get('Mięczaki')),
                )
                db.add(surowiec)
            db.commit()

        # 2. Seed Produkty
        print("Seeding produkty...")
        surowce_map = {s.nazwa: s.id for s in db.query(models.Surowiec).all()}
        
        with open('data/Produkty.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)
            for row in reader:
                if not row or len(row) < 2 or not row[0]:
                    continue
                ean = row[0]
                internal_id = ean[-6:] if len(ean) >= 6 else ean
                
                # Check if product exists
                existing = db.query(models.Produkt).filter(models.Produkt.ean == ean).first()
                if existing:
                    continue

                produkt = models.Produkt(
                    ean=ean,
                    internal_id=internal_id,
                    nazwa_pl=row[1],
                    nazwa_en=row[1]
                )
                db.add(produkt)
                db.flush()

                for i in range(3, min(36, len(row))):
                    val_str = row[i].replace(',', '.')
                    try:
                        val = float(val_str)
                    except ValueError:
                        val = 0
                    
                    if val > 0:
                        ing_name = headers[i]
                        sur_id = surowce_map.get(ing_name)
                        if sur_id:
                            skladnik = models.SkladnikProduktu(
                                produkt_ean=ean,
                                surowiec_id=sur_id,
                                procent=val,
                                kolejnosc=i
                            )
                            db.add(skladnik)
            db.commit()
            
        print("Seeding completed successfully.")

    except Exception as e:
        print(f"Error seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
