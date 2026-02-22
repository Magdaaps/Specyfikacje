"""
Test script to diagnose database save issues
"""
import sys
sys.path.insert(0, '.')

from database import SessionLocal
from models import Surowiec
import json

def test_surowiec_update():
    db = SessionLocal()
    try:
        # Get first surowiec
        surowiec = db.query(Surowiec).first()
        if not surowiec:
            print("ERROR: No surowiec found in database")
            return
        
        print(f"\n=== Testing Surowiec Update ===")
        print(f"ID: {surowiec.id}")
        print(f"Name: {surowiec.nazwa}")
        print(f"\nCurrent sklad_pl: {surowiec.sklad_pl}")
        print(f"Current sklad_procentowy: {surowiec.sklad_procentowy}")
        
        # Try to update
        test_value = "TEST: Kakao, cukier, mleko"
        test_json = json.dumps([{"nazwa": "Kakao", "procent": 50}])
        
        print(f"\n--- Attempting update ---")
        surowiec.sklad_pl = test_value
        surowiec.sklad_procentowy = test_json
        
        db.commit()
        db.refresh(surowiec)
        
        print(f"✓ COMMIT successful")
        print(f"New sklad_pl: {surowiec.sklad_pl}")
        print(f"New sklad_procentowy: {surowiec.sklad_procentowy}")
        
        # Verify by re-querying
        db.close()
        db = SessionLocal()
        verified = db.query(Surowiec).filter(Surowiec.id == surowiec.id).first()
        print(f"\n--- Verification (fresh query) ---")
        print(f"Verified sklad_pl: {verified.sklad_pl}")
        print(f"Verified sklad_procentowy: {verified.sklad_procentowy}")
        
        if verified.sklad_pl == test_value:
            print("\n✓✓✓ SUCCESS: Data persisted correctly!")
        else:
            print("\n✗✗✗ FAILURE: Data did not persist")
            
    except Exception as e:
        print(f"\n✗✗✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_surowiec_update()
