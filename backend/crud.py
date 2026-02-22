from sqlalchemy.orm import Session
import models, schemas

# Surowce
def get_surowiec(db: Session, surowiec_id: int):
    return db.query(models.Surowiec).filter(models.Surowiec.id == surowiec_id).first()

def get_surowce(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Surowiec).offset(skip).limit(limit).all()

def create_surowiec(db: Session, surowiec: schemas.SurowiecCreate):
    print(f"DEBUG: Creating new surowiec: {surowiec.nazwa}")
    db_surowiec = models.Surowiec(**surowiec.dict())
    db.add(db_surowiec)
    db.commit()
    db.refresh(db_surowiec)
    print(f"DEBUG: Successfully created surowiec with id={db_surowiec.id}")
    return db_surowiec

def update_surowiec(db: Session, surowiec_id: int, surowiec: schemas.SurowiecCreate):
    db_surowiec = get_surowiec(db, surowiec_id)
    if db_surowiec:
        try:
            update_dict = surowiec.dict()
            print(f"DEBUG: Updating surowiec {surowiec_id} with fields: {list(update_dict.keys())}")
            
            for key, value in update_dict.items():
                if hasattr(db_surowiec, key):
                    setattr(db_surowiec, key, value)
                    print(f"DEBUG: Set {key} = {value}")
                else:
                    print(f"WARNING: Surowiec model missing attribute: {key}")
            
            db.commit()
            db.refresh(db_surowiec)
            print(f"DEBUG: Successfully committed surowiec {surowiec_id}")
        except Exception as e:
            db.rollback()
            print(f"ERROR updating surowiec {surowiec_id}: {e}")
            import traceback
            traceback.print_exc()
            raise
    return db_surowiec

# Produkty
def get_produkt(db: Session, ean: str):
    return db.query(models.Produkt).filter(models.Produkt.ean == ean).first()

def get_produkty(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Produkt).offset(skip).limit(limit).all()

def create_produkt(db: Session, produkt: schemas.ProduktCreate):
    db_produkt = models.Produkt(**produkt.dict(exclude={"skladniki"}))
    db.add(db_produkt)
    db.flush()
    
    for sk in produkt.skladniki:
        db_sk = models.SkladnikProduktu(**sk.dict(), produkt_ean=db_produkt.ean)
        db.add(db_sk)
        
    db.commit()
    db.refresh(db_produkt)
    return db_produkt

def update_produkt(db: Session, ean: str, produkt: schemas.ProduktCreate):
    db_produkt = get_produkt(db, ean)
    if db_produkt:
        try:
            print(f"DEBUG: Updating product {ean} with {len(produkt.skladniki)} ingredients")
            
            # Update basic fields
            update_data = produkt.dict(exclude={"skladniki"})
            for key, value in update_data.items():
                setattr(db_produkt, key, value)
            
            # Update ingredients: delete old, create new
            # We use the ORIGINAL ean to delete old relations
            deleted_count = db.query(models.SkladnikProduktu).filter(models.SkladnikProduktu.produkt_ean == ean).delete()
            print(f"DEBUG: Deleted {deleted_count} old ingredients")
            
            # We use the NEW ean (from produkt object) for new relations
            new_ean = produkt.ean
            for idx, sk in enumerate(produkt.skladniki):
                db_skladnik = models.SkladnikProduktu(**sk.dict(), produkt_ean=new_ean)
                db.add(db_skladnik)
                print(f"DEBUG: Added ingredient {idx+1}: surowiec_id={sk.surowiec_id}, procent={sk.procent} to ean={new_ean}")
                
            db.commit()
            db.refresh(db_produkt)
            print(f"DEBUG: Successfully committed product {ean}")
        except Exception as e:
            db.rollback()
            print(f"ERROR updating product {ean}: {e}")
            import traceback
            traceback.print_exc()
            raise
    return db_produkt

def add_skladnik(db: Session, ean: str, skladnik: schemas.SkladnikCreate):
    db_skladnik = models.SkladnikProduktu(**skladnik.dict(), produkt_ean=ean)
    db.add(db_skladnik)
    db.commit()
    db.refresh(db_skladnik)
    return db_skladnik

def remove_skladniki(db: Session, ean: str):
    db.query(models.SkladnikProduktu).filter(models.SkladnikProduktu.produkt_ean == ean).delete()
    db.commit()
