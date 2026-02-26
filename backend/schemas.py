from pydantic import BaseModel
from typing import Optional, List

# Surowiec
class SurowiecBase(BaseModel):
    nazwa: str
    nazwa_en: Optional[str] = None
    kraj_pochodzenia: Optional[str] = None
    sklad_pl: Optional[str] = None
    sklad_en: Optional[str] = None
    kategoria: Optional[str] = "Inne"
    sklad_procentowy: Optional[str] = None
    pochodzenie_skladnikow: Optional[str] = None
    energia_kj: float = 0.0
    energia_kcal: float = 0.0
    tluszcz: float = 0.0
    kwasy_nasycone: float = 0.0
    weglowodany: float = 0.0
    cukry: float = 0.0
    bialko: float = 0.0
    sol: float = 0.0
    blonnik: float = 0.0
    
    alergen_gluten: str = "Nie zawiera"
    alergen_skorupiaki: str = "Nie zawiera"
    alergen_jaja: str = "Nie zawiera"
    alergen_ryby: str = "Nie zawiera"
    alergen_orzeszki_ziemne: str = "Nie zawiera"
    alergen_soja: str = "Nie zawiera"
    alergen_mleko: str = "Nie zawiera"
    alergen_orzechy: str = "Nie zawiera"
    alergen_seler: str = "Nie zawiera"
    alergen_gorczyca: str = "Nie zawiera"
    alergen_sezam: str = "Nie zawiera"
    alergen_dwutlenek_siarki: str = "Nie zawiera"
    alergen_lubin: str = "Nie zawiera"
    alergen_mieczaki: str = "Nie zawiera"

class SurowiecCreate(SurowiecBase):
    pass

class Surowiec(SurowiecBase):
    id: int

    class Config:
        from_attributes = True

# SkladnikProduktu
class SkladnikBase(BaseModel):
    surowiec_id: int
    procent: float
    kolejnosc: int

class SkladnikCreate(SkladnikBase):
    pass

class Skladnik(SkladnikBase):
    id: int
    surowiec: Surowiec

    class Config:
        from_attributes = True

# Produkt
class ProduktBase(BaseModel):
    ean: str
    ean_karton: Optional[str] = None
    internal_id: Optional[str] = None
    nazwa_pl: str
    nazwa_en: Optional[str] = None
    prawna_nazwa_pl: Optional[str] = None
    prawna_nazwa_en: Optional[str] = None
    kategoria: Optional[str] = None
    product_type: Optional[str] = "inne"
    masa_netto: Optional[str] = None
    image_url: Optional[str] = None
    
    # Organoleptyka
    organoleptyka_smak: Optional[str] = None
    organoleptyka_zapach: Optional[str] = None
    organoleptyka_kolor: Optional[str] = None
    organoleptyka_wyglad_zewnetrzny: Optional[str] = None
    organoleptyka_wyglad_na_przekroju: Optional[str] = None
    
    # Specyfikacja - Nowe sekcje
    warunki_przechowywania: Optional[str] = None
    termin_przydatnosci: Optional[str] = None
    wyrazenie_format_daty: Optional[str] = None
    informacje_dodatkowe: Optional[str] = None
    alergeny: Optional[str] = None
    
    # Nowe pola
    kod_cn: Optional[str] = None
    kod_pkwiu: Optional[str] = None
    certyfikaty: Optional[str] = None
    
    # Logistyka - Wymiary
    logistyka_wymiary_solo_h: float = 0.0
    logistyka_wymiary_solo_w: float = 0.0
    logistyka_wymiary_solo_d: float = 0.0
    logistyka_wymiary_jednostka_h: float = 0.0
    logistyka_wymiary_jednostka_w: float = 0.0
    logistyka_wymiary_jednostka_d: float = 0.0
    logistyka_wymiary_zbiorcze1_h: float = 0.0
    logistyka_wymiary_zbiorcze1_w: float = 0.0
    logistyka_wymiary_zbiorcze1_d: float = 0.0
    logistyka_wymiary_zbiorcze2_h: float = 0.0
    logistyka_wymiary_zbiorcze2_w: float = 0.0
    logistyka_wymiary_zbiorcze2_d: float = 0.0
    logistyka_wymiary_zbiorcze3_h: float = 0.0
    logistyka_wymiary_zbiorcze3_w: float = 0.0
    logistyka_wymiary_zbiorcze3_d: float = 0.0
    logistyka_rodzaj_palety: Optional[str] = None
    
    # Logistyka - Wagi
    logistyka_waga_netto_szt: float = 0.0
    logistyka_waga_brutto_szt: float = 0.0
    logistyka_waga_netto_zbiorcze: float = 0.0
    logistyka_waga_brutto_zbiorcze: float = 0.0
    logistyka_waga_netto_paleta: float = 0.0
    logistyka_waga_brutto_paleta: float = 0.0
    
    # Logistyka - Paletyzacja
    logistyka_sztuk_w_zbiorczym: int = 0
    logistyka_kartonow_na_warstwie: int = 0
    logistyka_warstw_na_palecie: int = 0
    logistyka_kartonow_na_palecie: int = 0
    logistyka_sztuk_na_palecie: int = 0
    logistyka_sztuk_na_warstwie: int = 0
    logistyka_wysokosc_palety: float = 0.0

class ProduktCreate(ProduktBase):
    skladniki: List[SkladnikBase] = []

class Produkt(ProduktBase):
    skladniki: List[Skladnik] = []

    class Config:
        from_attributes = True
