from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Surowiec(Base):
    __tablename__ = "surowce"

    id = Column(Integer, primary_key=True, index=True)
    nazwa = Column(String, unique=True, index=True)
    nazwa_en = Column(String)
    kraj_pochodzenia = Column(String)
    sklad_pl = Column(String) # Kolumna "Skład" ze zdjęcia 1
    sklad_en = Column(String)
    kategoria = Column(String, default="Inne")
    
    # Dane szczegółowe (JSON dla elastyczności)
    sklad_procentowy = Column(String) # JSON z procentami ze zdjęcia 2
    pochodzenie_skladnikow = Column(String) # JSON z krajami ze zdjęcia 4 i 5
    
    # Nutrition
    energia_kj = Column(Float, default=0.0)
    energia_kcal = Column(Float, default=0.0)
    tluszcz = Column(Float, default=0.0)
    kwasy_nasycone = Column(Float, default=0.0)
    weglowodany = Column(Float, default=0.0)
    cukry = Column(Float, default=0.0)
    bialko = Column(Float, default=0.0)
    sol = Column(Float, default=0.0)
    blonnik = Column(Float, default=0.0)

    # Allergens (JSON or columns - for simplicity let's use columns for the 14 main ones)
    alergen_gluten = Column(String, default="Nie zawiera")
    alergen_skorupiaki = Column(String, default="Nie zawiera")
    alergen_jaja = Column(String, default="Nie zawiera")
    alergen_ryby = Column(String, default="Nie zawiera")
    alergen_orzeszki_ziemne = Column(String, default="Nie zawiera")
    alergen_soja = Column(String, default="Nie zawiera")
    alergen_mleko = Column(String, default="Nie zawiera")
    alergen_orzechy = Column(String, default="Nie zawiera")
    alergen_seler = Column(String, default="Nie zawiera")
    alergen_gorczyca = Column(String, default="Nie zawiera")
    alergen_sezam = Column(String, default="Nie zawiera")
    alergen_dwutlenek_siarki = Column(String, default="Nie zawiera")
    alergen_lubin = Column(String, default="Nie zawiera")
    alergen_mieczaki = Column(String, default="Nie zawiera")

class Produkt(Base):
    __tablename__ = "produkty"

    ean = Column(String(13), primary_key=True, index=True) # EAN Sztuka
    ean_karton = Column(String(13)) # EAN Karton
    internal_id = Column(String(6))
    nazwa_pl = Column(String)
    nazwa_en = Column(String)
    prawna_nazwa_pl = Column(String)
    prawna_nazwa_en = Column(String)
    kategoria = Column(String)
    product_type = Column(String, default="inne")  # lizaki | figurki | tabliczki | inne
    masa_netto = Column(String)
    image_url = Column(String) # Path to uploaded image
    
    # Timestamps
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Organoleptyka
    organoleptyka_smak = Column(String)
    organoleptyka_zapach = Column(String)
    organoleptyka_kolor = Column(String)
    organoleptyka_wyglad_zewnetrzny = Column(String)
    organoleptyka_wyglad_na_przekroju = Column(String)
    
    # Specyfikacja - Nowe sekcje
    warunki_przechowywania = Column(String)
    termin_przydatnosci = Column(String)
    wyrazenie_format_daty = Column(String)
    informacje_dodatkowe = Column(String)
    alergeny = Column(String) # JSON z manualnie ustawionymi statusami alergenów
    
    # Rozszerzenie Dane Ogólne
    kod_cn = Column(String)
    kod_pkwiu = Column(String)
    certyfikaty = Column(String) # JSON list of objects [{rodzaj, coid, data_waznosci}]
    
    # Logistyka - Wymiary
    logistyka_wymiary_solo_h = Column(Float, default=0.0)
    logistyka_wymiary_solo_w = Column(Float, default=0.0)
    logistyka_wymiary_solo_d = Column(Float, default=0.0)
    logistyka_wymiary_jednostka_h = Column(Float, default=0.0)
    logistyka_wymiary_jednostka_w = Column(Float, default=0.0)
    logistyka_wymiary_jednostka_d = Column(Float, default=0.0)
    logistyka_wymiary_zbiorcze1_h = Column(Float, default=0.0)
    logistyka_wymiary_zbiorcze1_w = Column(Float, default=0.0)
    logistyka_wymiary_zbiorcze1_d = Column(Float, default=0.0)
    logistyka_wymiary_zbiorcze2_h = Column(Float, default=0.0)
    logistyka_wymiary_zbiorcze2_w = Column(Float, default=0.0)
    logistyka_wymiary_zbiorcze2_d = Column(Float, default=0.0)
    logistyka_wymiary_zbiorcze3_h = Column(Float, default=0.0)
    logistyka_wymiary_zbiorcze3_w = Column(Float, default=0.0)
    logistyka_wymiary_zbiorcze3_d = Column(Float, default=0.0)
    logistyka_rodzaj_palety = Column(String)
    
    # Logistyka - Wagi
    logistyka_waga_netto_szt = Column(Float, default=0.0)
    logistyka_waga_brutto_szt = Column(Float, default=0.0)
    logistyka_waga_netto_zbiorcze = Column(Float, default=0.0)
    logistyka_waga_brutto_zbiorcze = Column(Float, default=0.0)
    logistyka_waga_netto_paleta = Column(Float, default=0.0)
    logistyka_waga_brutto_paleta = Column(Float, default=0.0)
    
    # Logistyka - Paletyzacja
    logistyka_sztuk_w_zbiorczym = Column(Integer, default=0)
    logistyka_kartonow_na_warstwie = Column(Integer, default=0)
    logistyka_warstw_na_palecie = Column(Integer, default=0)
    logistyka_kartonow_na_palecie = Column(Integer, default=0)
    logistyka_sztuk_na_palecie = Column(Integer, default=0)
    logistyka_sztuk_na_warstwie = Column(Integer, default=0)
    logistyka_wysokosc_palety = Column(Float, default=0.0)
    
    skladniki = relationship("SkladnikProduktu", back_populates="produkt", cascade="all, delete-orphan")

class SkladnikProduktu(Base):
    __tablename__ = "skladniki_produktu"

    id = Column(Integer, primary_key=True, index=True)
    produkt_ean = Column(String(13), ForeignKey("produkty.ean"))
    surowiec_id = Column(Integer, ForeignKey("surowce.id"))
    procent = Column(Float)
    kolejnosc = Column(Integer)

    produkt = relationship("Produkt", back_populates="skladniki")
    surowiec = relationship("Surowiec")

class Slownik(Base):
    __tablename__ = "slownik"
    id = Column(Integer, primary_key=True, index=True)
    kategoria = Column(String) # "alergen", "kraj", "jednostka", "nazwa"
    pl = Column(String)
    en = Column(String)
