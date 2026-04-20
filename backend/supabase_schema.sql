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
