# Projekt: Aplikacja do tworzenia kart produktu (PL/EN)

## Założenia globalne
- Jedynym kluczem produktu jest EAN sztuki (13 cyfr).
- Wewnętrzne ID (`internal_id`) = 6 ostatnich cyfr EAN.
- Dane EN generowane automatycznie na podstawie słowników.
- Karty produktu generowane jako dwa osobne pliki XLS (PL i EN).
- Układ kart identyczny jak w obecnym Excelu.
- Dane logistyczne pobierane z pliku Excel na SharePoint.
- Zapis kart na SharePoint tylko po wyborze lokalizacji przez użytkownika.

---

# ETAP 0 — Przygotowanie i fundamenty projektu

## 0.1 Analiza wejściowa
- [ ] Przeanalizować plik „BAZA_SUROWCÓW - Wszystkie surowce.xlsm”
- [ ] Zidentyfikować wszystkie arkusze i ich role
- [ ] Wypisać wszystkie pola występujące w:
  - [ ] Surowce
  - [ ] Produkty
  - [ ] Baza_produktów
  - [ ] Karta produktu (PL)
  - [ ] Product specification (EN)
  - [ ] SLOWNIKI
- [ ] Przeanalizować plik „Logistyka + dane produktów.xlsx”
- [ ] Zidentyfikować kolumny logistyczne oraz ich znaczenie biznesowe

## 0.2 Decyzje architektoniczne
- [ ] Potwierdzić EAN jako jedyny klucz produktu
- [ ] Zdefiniować regułę generowania `internal_id`
- [ ] Zdefiniować strategię tłumaczeń PL→EN (słowniki, fallback)
- [ ] Zdefiniować strategię eksportu XLS (szablony + mapowanie)

---

# ETAP 1 — Model danych (odporność na zmiany)

## 1.1 Encja: Surowiec
- [ ] Zdefiniować strukturę danych surowca
- [ ] Wyodrębnić wartości odżywcze jako osobne pola numeryczne
- [ ] Zidentyfikować „składniki-alergeny” obecnie zapisane jako kolumny
- [ ] Zaprojektować tabelę relacyjną `surowiec_skladnik`
- [ ] Zaprojektować tabelę słownikową `skladnik`
- [ ] Zaprojektować tabelę słownikową `alergen`
- [ ] Dodać pole kraju pochodzenia surowca

## 1.2 Encja: Produkt
- [ ] Zdefiniować pole `ean_sztuki` (unikalne)
- [ ] Zdefiniować pole `internal_id` (6 ostatnich cyfr EAN)
- [ ] Zdefiniować pola nazw produktu (handlowa, prawna)
- [ ] Zdefiniować pola opisowe (organoleptyka, warunki, termin itd.)
- [ ] Zdefiniować relację do składu produktu

## 1.3 Encja: Skład produktu
- [ ] Utworzyć encję `produkt_surowiec`
- [ ] Dodać pole procentowe
- [ ] Dodać walidację sumy procentów = 100
- [ ] Dodać kolejność wyświetlania składników

## 1.4 Encja: Logistyka
- [ ] Zdefiniować encję `logistyka`
- [ ] Podzielić dane na sekcje:
  - [ ] sztuka
  - [ ] opakowanie jednostkowe
  - [ ] karton
  - [ ] paleta
- [ ] Ustalić pola ilościowe (szt/karton/paleta itd.)
- [ ] Znormalizować jednostki (cm, kg → liczby)

---

# ETAP 2 — Słowniki i tłumaczenia PL → EN

## 2.1 Słowniki systemowe
- [ ] Utworzyć słownik nazw składników (PL → EN)
- [ ] Utworzyć słownik alergenów (PL → EN)
- [ ] Utworzyć słownik krajów pochodzenia (PL → EN)
- [ ] Utworzyć słownik jednostek miar (PL → EN)
- [ ] Utworzyć słownik stałych etykiet karty (nagłówki, sekcje)

## 2.2 Mechanizm tłumaczeń
- [ ] Zaimplementować mechanizm zamiany terminów PL → EN
- [ ] Obsłużyć odmiany / aliasy nazw
- [ ] Zdefiniować fallback (brak tłumaczenia → PL + ostrzeżenie)
- [ ] Zaimplementować raport brakujących tłumaczeń

---

# ETAP 3 — Interfejs użytkownika (CRUD)

## 3.1 Surowce
- [ ] Widok listy surowców
- [ ] Wyszukiwarka po nazwie
- [ ] Filtrowanie po alergenach / kraju
- [ ] Formularz dodawania surowca
- [ ] Formularz edycji surowca
- [ ] Walidacje pól obowiązkowych

## 3.2 Produkty
- [ ] Widok listy produktów
- [ ] Wyszukiwanie po EAN / nazwie
- [ ] Formularz dodawania produktu
- [ ] Formularz edycji produktu
- [ ] Edytor składu (dodaj/usuń surowiec, %)
- [ ] Walidacja sumy procentów
- [ ] Przycisk „Duplikuj produkt”
- [ ] Wymuszenie nowego EAN przy duplikacji

---

# ETAP 4 — Logika biznesowa (automaty)

## 4.1 Wartości odżywcze
- [ ] Obliczanie wartości na podstawie składu
- [ ] Zaokrąglenia zgodne z obecnym Excelem
- [ ] Walidacja wyników

## 4.2 Skład produktu
- [ ] Generowanie tekstu składu
- [ ] Pogrubianie alergenów
- [ ] Kolejność składników wg udziału

## 4.3 Alergeny i kraje
- [ ] Agregacja alergenów z surowców
- [ ] Eliminacja duplikatów
- [ ] Agregacja krajów pochodzenia

---

# ETAP 5 — Integracja z SharePoint Excel (Logistyka)

## 5.1 Konfiguracja źródła
- [ ] Wskazanie pliku Excel na SharePoint
- [ ] Wybór arkusza
- [ ] Zdefiniowanie wiersza nagłówków

## 5.2 Mapowanie kolumn
- [ ] Mapowanie EAN
- [ ] Mapowanie danych sztuki
- [ ] Mapowanie danych kartonu
- [ ] Mapowanie danych palety
- [ ] Zapis konfiguracji mapowania

## 5.3 Import danych
- [ ] Import danych do bazy
- [ ] Normalizacja jednostek
- [ ] Obsługa błędów (brak EAN, duplikaty)
- [ ] Przycisk „Odśwież import”

## 5.4 Podpinanie do produktu
- [ ] Automatyczne dopasowanie po EAN
- [ ] Wyświetlenie danych logistycznych w produkcie
- [ ] Obsługa braku dopasowania

---

# ETAP 6 — Generator kart XLS (PL + EN)

## 6.1 Szablony
- [ ] Przygotować szablon PL (na bazie obecnej karty)
- [ ] Przygotować szablon EN (identyczny layout)
- [ ] Zablokować strukturę szablonów

## 6.2 Mapowanie danych → komórki
- [ ] Przepisać mapowanie z Excela do konfiguracji aplikacji
- [ ] Zmapować wszystkie pola PL
- [ ] Zmapować wszystkie pola EN
- [ ] Przetestować kompletność mapowania

## 6.3 Generowanie plików
- [ ] Generowanie XLS PL
- [ ] Generowanie XLS EN
- [ ] Walidacja poprawności danych w plikach

---

# ETAP 7 — Zapis i eksport

## 7.1 Eksport lokalny
- [ ] Pobieranie plików na komputer

## 7.2 Zapis na SharePoint
- [ ] Wybór site
- [ ] Wybór biblioteki
- [ ] Wybór folderu
- [ ] Możliwość utworzenia nowego folderu
- [ ] Konfigurowalna nazwa plików
- [ ] Zapis tylko po potwierdzeniu użytkownika

---

# ETAP 8 — Walidacje, testy i gotowość produkcyjna

## 8.1 Walidacje
- [ ] Walidacja EAN (13 cyfr)
- [ ] Walidacja sumy składu
- [ ] Walidacja obecności logistyki przed eksportem
- [ ] Walidacja kompletności tłumaczeń

## 8.2 Testy
- [ ] Testy jednostkowe obliczeń
- [ ] Testy generowania XLS
- [ ] Testy integracji SharePoint
- [ ] Testy regresji względem obecnego Excela

## 8.3 Gotowość
- [ ] Dokumentacja użytkownika
- [ ] Checklisty dla działu jakości
- [ ] Plan migracji danych z Excela
