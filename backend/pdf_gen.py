from xhtml2pdf import pisa, default as pisa_default
from io import BytesIO
import logic
import models
import json
import os
import re
import unicodedata
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Company Info (Placeholders as per requirements)
COMPANY_INFO = {
    "name": "Adikam Sp. z o.o.",
    "address": "ul. Szlachecka 42, 32-050 Borek Szlachecki",
    "nip": "",
    "www": "",
    "email": ""
}

# ---------------------------------------------------------------------------
# Load EN translations dictionary
# ---------------------------------------------------------------------------
_DICT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations_en.json")
_TRANSLATIONS: dict = {}
try:
    with open(_DICT_PATH, encoding="utf-8") as _f:
        _TRANSLATIONS = json.load(_f)
except Exception:
    pass

_ALLERGEN_PRESENCE_EN: dict = _TRANSLATIONS.get("allergen_presence", {})
_ALLERGENS_EN: dict = _TRANSLATIONS.get("allergens", {})
_NUTRITION_LABELS_EN: dict = _TRANSLATIONS.get("nutrition_labels", {})
_DOCUMENT_SECTIONS_EN: dict = _TRANSLATIONS.get("document_sections", {})
_DOCUMENT_FIELDS_EN: dict = _TRANSLATIONS.get("document_fields", {})
_STANDARD_TEXTS_EN: dict = _TRANSLATIONS.get("standard_texts", {})
_COUNTRIES_EN: dict = _TRANSLATIONS.get("countries", {})

# ---------------------------------------------------------------------------
# Master phrase translator (PL → EN)
# Used for free-text fields: organoleptyka, storage, shelf life, ingredients
# Built from all relevant dictionary sections; sorted longest-first so that
# "serwatka w proszku (z mleka)" is matched before "serwatka".
#
# NOTE: document_fields is intentionally excluded – it contains UI labels
# (e.g. "Smak" → "Taste") that must not be applied to content text.
# ---------------------------------------------------------------------------
_PL_WORD_CHARS = r"a-zA-ZąęóśźżćńłĄĘÓŚŹŻĆŃŁ"


def _word_boundary_pattern(phrase: str) -> re.Pattern:
    """Return a compiled regex that matches *phrase* only at word boundaries.

    Uses Polish-aware lookbehind/lookahead so that e.g. 'kakao' does not
    match inside 'kakaowy', and 'smak' does not match inside 'posmaków'.
    """
    escaped = re.escape(phrase)
    prefix = f"(?<![{_PL_WORD_CHARS}])" if phrase and re.match(f"[{_PL_WORD_CHARS}]", phrase[0]) else ""
    suffix = f"(?![{_PL_WORD_CHARS}])" if phrase and re.match(f"[{_PL_WORD_CHARS}]", phrase[-1]) else ""
    return re.compile(prefix + escaped + suffix, re.IGNORECASE)


def _build_master_translator() -> list:
    combined: dict = {}
    for section in [
        "standard_texts",
        "ingredients_raw",
        "chocolate_types",
        "packaging_terms",
        "allergen_presence",
        # document_fields excluded: UI labels only, not content words
        "seasons_occasions",
    ]:
        combined.update(_TRANSLATIONS.get(section, {}))
    # Sort by PL phrase length descending – longest phrase wins
    pairs = sorted(combined.items(), key=lambda kv: len(kv[0]), reverse=True)
    # Pre-compile with word-boundary patterns
    return [(en, _word_boundary_pattern(pl)) for pl, en in pairs]


_MASTER_TRANSLATOR: list = _build_master_translator()


# ---------------------------------------------------------------------------
# Confectionery technical terminology – HARDCODED, highest priority.
#
# These substitutions are applied BEFORE the general phrase translator so
# that the correct industry term "compound chocolate" is always used for
# all inflected forms of the Polish word "masa", regardless of what is
# currently cached in the JSON dictionary at server startup.
#
# Rule: NEVER translate "masa" (confectionery) as "mass".  The correct
# English term is always "compound chocolate".
#
# Entries are ordered longest-first so that specific phrases such as
# "masa na bazie białej czekolady" are matched before the bare "masa".
# ---------------------------------------------------------------------------
_TECH_TERMS: list[tuple[str, str]] = [
    # Full compound phrases first (longest → shortest).
    # IGNORECASE is applied by _word_boundary_pattern, so no need to list
    # capitalised variants separately – they would collide with case-preserving
    # lowercase replacements below.
    ("masa na bazie białej czekolady",   "white chocolate-based compound chocolate"),
    ("masą na bazie białej czekolady",   "white chocolate-based compound chocolate"),
    ("masa o smaku czekolady mlecznej",  "milk chocolate-flavoured compound chocolate"),
    ("masa o smaku białej czekolady",    "white chocolate-flavoured compound chocolate"),
    ("masa o smaku mleczno-kakaowym",    "milk-cocoa flavoured compound chocolate"),
    ("masa o smaku mlecznym",            "milk-flavoured compound chocolate"),
    ("dla masy",  "for compound chocolate"),
    ("dla mas",   "for compound chocolate"),
    # Single-word inflected forms (lowercase; IGNORECASE covers Masy/MASY etc.)
    ("masy",   "compound chocolate"),
    ("masą",   "compound chocolate"),
    ("masie",  "compound chocolate"),
    ("masę",   "compound chocolate"),
    ("masa",   "compound chocolate"),
    ("mas",    "compound chocolate"),
]

_TECH_TERMS_COMPILED: list[tuple[str, re.Pattern]] = [
    (en, _word_boundary_pattern(pl)) for pl, en in _TECH_TERMS
]


def _apply_tech_dictionary(text: str) -> str:
    """Apply confectionery technical terminology substitutions (highest priority).

    Runs BEFORE the general phrase translator to enforce correct industry
    terms.  Ensures all inflected forms of 'masa' → 'compound chocolate',
    never 'mass'.
    """
    result = text
    for en, pattern in _TECH_TERMS_COMPILED:
        try:
            result = pattern.sub(en, result)
        except re.error:
            continue
    return result


def _build_product_name_translator() -> list:
    """Translator for product names – extends master with product_names and product_types.

    product_names contains specific full-product descriptions (e.g. complete lollipop names).
    product_types contains generic type names (Lizak → Lollipop, Figurka → Figurine).
    Both are critical for correct product name translation but must NOT be used for
    ingredient/organoleptic text (to avoid over-matching raw material names).
    """
    combined: dict = {}
    for section in [
        "product_names",
        "product_types",
        "chocolate_types",
        "packaging_terms",
        "seasons_occasions",
        "standard_texts",
    ]:
        combined.update(_TRANSLATIONS.get(section, {}))
    pairs = sorted(combined.items(), key=lambda kv: len(kv[0]), reverse=True)
    return [(en, _word_boundary_pattern(pl)) for pl, en in pairs]


_PRODUCT_NAME_TRANSLATOR: list = _build_product_name_translator()


def _translate_product_name(pl_name: str) -> str:
    """Translate a product name PL→EN using the product name dictionary.

    Uses longest-first word-boundary phrase substitution across product_names,
    product_types, chocolate_types, packaging_terms, seasons_occasions and
    standard_texts sections.

    Logs a warning if Polish characters remain after translation.
    """
    if not pl_name:
        return pl_name
    result = pl_name.strip()
    for en, pattern in _PRODUCT_NAME_TRANSLATOR:
        try:
            result = pattern.sub(en, result)
        except re.error:
            continue
    if _PL_CHARS_RE.search(result):
        logger.warning(
            "EN PDF: untranslated Polish chars in product name — %r → %r",
            pl_name[:100], result[:100],
        )
    return result


def _translate_any_text(text: str) -> str:
    """Translate Polish text → English using whole-word phrase substitution.

    Processes longest phrases first (pre-compiled, word-boundary aware).
    Partial word matches (e.g. 'kakao' inside 'kakaowy') are prevented by
    the word-boundary patterns.
    """
    if not text:
        return text
    result = text
    for en, pattern in _MASTER_TRANSLATOR:
        try:
            result = pattern.sub(en, result)
        except re.error:
            continue
    return result

# ---------------------------------------------------------------------------
# Allergen maps – PL
# ---------------------------------------------------------------------------
ALLERGEN_MAP_PL = {
    'gluten': 'Gluten',
    'skorupiaki': 'Skorupiaki',
    'jaja': 'Jaja',
    'ryby': 'Ryby',
    'orzeszki_ziemne': 'Orzeszki ziemne',
    'soja': 'Soja',
    'mleko': 'Mleko',
    'orzechy': 'Orzechy',
    'seler': 'Seler',
    'gorczyca': 'Gorczyca',
    'sezam': 'Sezam',
    'dwutlenek_siarki': 'Dwutlenek siarki i siarczyny',
    'lubin': 'Łubin',
    'mieczaki': 'Mięczaki',
}

ALLERGEN_MAP_PDF = {
    'gluten': 'Zboża zawierające gluten, tj. pszenica (w tym orkisz i pszenica), żyto, jęczmień,<br/>owies lub ich odmiany',
    'skorupiaki': 'Skorupiaki i produkty pochodne',
    'jaja': 'Jaja i produkty pochodne',
    'ryby': 'Ryby i produkty pochodne, z wyjątkiem: żelatyny rybnej',
    'orzeszki_ziemne': 'Orzeszki ziemne (arachidowe) i produkty pochodne',
    'soja': 'Soja i produkty pochodne',
    'mleko': 'Mleko i produkty pochodne (łącznie z laktozą), z wyjątkiem: a) serwatki b) laktiolu',
    'orzechy': 'Orzechy i produkty pochodne',
    'seler': 'Seler i produkty pochodne',
    'gorczyca': 'Gorczyca i produkty pochodne',
    'sezam': 'Nasiona sezamu i produkty pochodne',
    'dwutlenek_siarki': 'Dwutlenek siarki i siarczyny w stężeniach powyżej 10 mg/kg lub 10 mg/litr w przeliczeniu na całkowitą zawartość SO2 dla produktów w postaci gotowej bezpośrednio do spożycia',
    'lubin': 'Łubin i produkty pochodne',
    'mieczaki': 'Mięczaki i produkty pochodne',
}

# ---------------------------------------------------------------------------
# Allergen maps – EN (built from JSON dictionary)
# ---------------------------------------------------------------------------
# Maps key → full EN description, via the PL description as lookup key
def _build_allergen_pdf_en() -> dict:
    result = {}
    for key, pl_text in ALLERGEN_MAP_PDF.items():
        # Strip any <br/> tags for the lookup
        pl_lookup = pl_text.replace('<br/>', ' ').replace('<br>', ' ')
        # Try exact match first, then normalised
        en_text = _ALLERGENS_EN.get(pl_lookup)
        if not en_text:
            # Fallback: find by startswith
            for pl_key, en_val in _ALLERGENS_EN.items():
                if pl_lookup.startswith(pl_key[:30]) or pl_key.startswith(pl_lookup[:30]):
                    en_text = en_val
                    break
        result[key] = en_text or pl_lookup
    return result

ALLERGEN_MAP_PDF_EN = _build_allergen_pdf_en()


def _status_to_css_class(status: str) -> str:
    normalized = unicodedata.normalize("NFKD", status or "")
    normalized = normalized.encode("ascii", "ignore").decode("ascii").lower()
    if "zawiera" in normalized:
        return "contains"
    if "moze" in normalized and "zawier" in normalized:
        return "may-contain"
    return "other"


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_REGULAR = os.path.join(_BASE_DIR, "fonts", "arial.ttf")
FONT_BOLD = os.path.join(_BASE_DIR, "fonts", "arialbd.ttf")

_fonts_registered = False


def _register_fonts():
    """Register Arial TTF with ReportLab and override xhtml2pdf's default font map.

    xhtml2pdf maps 'arial' → 'Helvetica' by default (no Polish chars).
    We replace that mapping with our TTF-registered Arial.
    No @font-face / temp files needed – bypasses the Windows NamedTemporaryFile bug.
    """
    global _fonts_registered
    if _fonts_registered:
        return

    if os.path.exists(FONT_REGULAR):
        pdfmetrics.registerFont(TTFont("Arial", FONT_REGULAR))
        addMapping("Arial", 0, 0, "Arial")
        addMapping("Arial", 0, 1, "Arial")

    if os.path.exists(FONT_BOLD):
        pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_BOLD))
        addMapping("Arial", 1, 0, "Arial-Bold")
        addMapping("Arial", 1, 1, "Arial-Bold")

    # Override xhtml2pdf's default mapping so CSS font-family: Arial uses our TTF
    pisa_default.DEFAULT_FONT["arial"] = "Arial"
    pisa_default.DEFAULT_FONT["arial unicode ms"] = "Arial"

    _fonts_registered = True


# ---------------------------------------------------------------------------
# Allergen auto-bolding – PL
# ---------------------------------------------------------------------------
_PL_CHARS = r"a-zA-ZąęóśźżćńłĄĘÓŚŹŻĆŃŁ"

_ALLERGEN_BOLD_WORDS = [
    # Multi-word phrases first (longest → shortest prevents partial overlap)
    "orzeszki arachidowe",
    "orzechy laskowe",
    # Single words
    "mleko", "mleka", "mleczne", "mleczny",
    "soja", "soi", "sojowa", "sojowe",
    "gluten", "pszenna",
    "jaja", "jaj",
    "orzechy", "migdały", "pistacje", "pisatacje",
    "sezam",
]

_ALLERGEN_PATTERN_PDF = re.compile(
    r"(?<![" + _PL_CHARS + r"])("
    + "|".join(map(re.escape, sorted(_ALLERGEN_BOLD_WORDS, key=len, reverse=True)))
    + r")(?![" + _PL_CHARS + r"])",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Allergen auto-bolding – EN
# ---------------------------------------------------------------------------
_EN_CHARS = r"a-zA-Z"

_ALLERGEN_BOLD_WORDS_EN = [
    "peanuts",
    "tree nuts", "hazelnuts", "almonds", "pistachios",
    "milk", "lactose",
    "soy", "soybeans",
    "gluten", "wheat", "rye", "barley", "oats",
    "eggs",
    "nuts",
    "sesame",
    "crustaceans",
    "fish",
    "celery",
    "mustard",
    "sulphites", "sulphur dioxide",
    "lupin",
    "molluscs",
]

_ALLERGEN_PATTERN_PDF_EN = re.compile(
    r"(?<![" + _EN_CHARS + r"])("
    + "|".join(map(re.escape, sorted(_ALLERGEN_BOLD_WORDS_EN, key=len, reverse=True)))
    + r")(?![" + _EN_CHARS + r"])",
    re.IGNORECASE,
)


def _bold_allergens_html(text: str, lang: str = "pl") -> str:
    """Wrap allergen words in <strong> tags (input is plain text, output is HTML)."""
    if not text:
        return text
    pattern = _ALLERGEN_PATTERN_PDF_EN if lang == "en" else _ALLERGEN_PATTERN_PDF
    return pattern.sub(r"<strong>\1</strong>", text)


def _translate_status(status: str, lang: str) -> str:
    """Translate allergen presence status to target language."""
    if lang == "pl" or not status:
        return status
    return _ALLERGEN_PRESENCE_EN.get(status, status)


def _translate_text(text: str, lang: str) -> str:
    """Translate a free-text field to English.

    Strategy:
    1. Exact match in standard_texts (fastest, most precise).
    2. Confectionery technical terminology (hardcoded, highest priority).
       Ensures 'masa' → 'compound chocolate', never 'mass'.
    3. General whole-word phrase substitution via master translator.
    """
    if lang == "pl" or not text:
        return text
    stripped = text.strip()
    # Step 1 – exact match
    exact = _STANDARD_TEXTS_EN.get(stripped)
    if exact:
        return exact
    # Step 2 – technical terminology (must run before general substitution)
    result = _apply_tech_dictionary(stripped)
    # Step 3 – general phrase-by-phrase substitution (word-boundary safe)
    return _translate_any_text(result)


# ---------------------------------------------------------------------------
# Polish character validation for EN PDF output
# ---------------------------------------------------------------------------
_PL_CHARS_RE = re.compile(r"[ąęóśźżćńłĄĘÓŚŹŻĆŃŁ]")


def _validate_no_polish_chars(text: str, field_name: str) -> str:
    """Log an error if translated EN text still contains Polish characters.

    Returns the text unchanged so rendering continues (PDF still generated).
    """
    if text and _PL_CHARS_RE.search(text):
        logger.error(
            "EN PDF generation error: Polish characters in field %r — %r",
            field_name,
            text[:200],
        )
    return text


# ---------------------------------------------------------------------------
# Terminology validation – "mass" must never appear in EN PDF output
# (correct term: "compound chocolate")
# ---------------------------------------------------------------------------
# Matches "mass" in confectionery-problematic contexts:
#   "for mass", "of mass", "the mass", "mass," – but NOT "Xmass" / "biomass"
_EN_INVALID_MASS_RE = re.compile(
    r'(?<!\w)(?:for|of|the)\s+mass\b|'   # "for mass", "of mass", "the mass"
    r'\bmass[,\.]',                        # "mass," or "mass."
    re.IGNORECASE,
)


def _validate_no_mass_term(text: str, field_name: str) -> str:
    """Log an error if 'mass' appears where 'compound chocolate' is expected.

    Returns the text unchanged so rendering continues (PDF still generated).
    """
    if text and _EN_INVALID_MASS_RE.search(text):
        logger.error(
            "EN PDF terminology error: 'mass' found in field %r "
            "(should be 'compound chocolate') — %r",
            field_name,
            text[:200],
        )
    return text


def _translate_country(name: str) -> str:
    """Translate a single country name PL→EN using the countries dictionary.

    Falls back to the original value and logs a warning for missing entries.
    """
    stripped = name.strip()
    if not stripped:
        return stripped
    translated = _COUNTRIES_EN.get(stripped)
    if translated:
        return translated
    # Case-insensitive fallback
    stripped_lower = stripped.lower()
    for pl, en in _COUNTRIES_EN.items():
        if pl.lower() == stripped_lower:
            return en
    logger.warning("Missing country translation (PL→EN): %r", stripped)
    return stripped


def _translate_countries(countries: list, lang: str) -> list:
    """Translate a list of country names to English.

    Each element may itself be a comma-separated string – such strings are
    split, each part translated individually, then rejoined.
    """
    if lang == "pl":
        return countries
    result = []
    for entry in countries:
        # Handle a single string that contains multiple comma-separated names
        parts = [p.strip() for p in entry.split(",") if p.strip()]
        translated_parts = [_translate_country(p) for p in parts]
        result.append(", ".join(translated_parts))
    return result


def _link_callback(uri, rel):
    """Resolve file:/// URIs so xhtml2pdf can read local images."""
    if uri.startswith("file:///"):
        return uri[8:]
    return uri


def generate_pdf(produkt: models.Produkt, lang: str = "pl"):
    # ---------------------------------------------------------------------------
    # Translation helpers
    # ---------------------------------------------------------------------------
    def _s(pl_key: str) -> str:
        """Translate a document_sections key."""
        if lang == "pl":
            return pl_key
        return _DOCUMENT_SECTIONS_EN.get(pl_key, pl_key)

    def _f(pl_key: str) -> str:
        """Translate a document_fields key."""
        if lang == "pl":
            return pl_key
        return _DOCUMENT_FIELDS_EN.get(pl_key, pl_key)

    def _n(pl_key: str) -> str:
        """Translate a nutrition_labels key."""
        if lang == "pl":
            return pl_key
        return _NUTRITION_LABELS_EN.get(pl_key, pl_key)

    def _orga(pl_value: str | None, field: str) -> str:
        """Translate an organoleptika/spec field and validate EN output quality."""
        translated = _translate_text(pl_value or "", lang)
        if lang == "en":
            _validate_no_polish_chars(translated, field)
            _validate_no_mass_term(translated, field)
        return translated

    # Select allergen map
    allergen_pdf_map = ALLERGEN_MAP_PDF_EN if lang == "en" else ALLERGEN_MAP_PDF

    # Product name and legal name
    # For EN: use *_en field ONLY if it is genuinely English – i.e. not a copy
    # of the PL value.  We detect copies by stripping diacritics from both sides
    # and comparing (case-insensitive); identical stripped forms → it is a copy.
    def _is_genuine_en(en_val: str, pl_val: str) -> bool:
        if not en_val:
            return False
        if _PL_CHARS_RE.search(en_val):
            return False  # Contains Polish diacritics → definitely PL
        pl_stripped = unicodedata.normalize("NFD", pl_val or "")
        pl_stripped = "".join(c for c in pl_stripped if unicodedata.category(c) != "Mn").lower()
        en_stripped = unicodedata.normalize("NFD", en_val)
        en_stripped = "".join(c for c in en_stripped if unicodedata.category(c) != "Mn").lower()
        return en_stripped != pl_stripped  # Different → genuine translation

    if lang == "en":
        _raw_name_en = (produkt.nazwa_en or "").strip()
        if _is_genuine_en(_raw_name_en, produkt.nazwa_pl or ""):
            product_name = _raw_name_en
        else:
            product_name = _translate_product_name(produkt.nazwa_pl or "")
            _validate_no_polish_chars(product_name, "nazwa_en (dynamically translated)")

        _raw_legal_en = (produkt.prawna_nazwa_en or "").strip()
        if _is_genuine_en(_raw_legal_en, produkt.prawna_nazwa_pl or ""):
            legal_name = _raw_legal_en
        else:
            _pl_legal = (produkt.prawna_nazwa_pl or "").strip()
            legal_name = _translate_product_name(_pl_legal)
            _validate_no_polish_chars(legal_name, "prawna_nazwa_en (dynamically translated)")
            if _pl_legal and legal_name == _pl_legal:
                logger.warning(
                    "EN PDF: no translation found for prawna_nazwa_pl=%r – legal name will show in Polish",
                    _pl_legal[:100],
                )
    else:
        product_name = produkt.nazwa_pl or ""
        legal_name = produkt.prawna_nazwa_pl or ""

    # Footer page text
    page_label = "Page" if lang == "en" else "Strona"
    of_label = "of" if lang == "en" else "z"

    # Prepare data
    nutrition = logic.calculate_nutrition(produkt)
    allergens = logic.aggregate_allergens(produkt)
    ingredients_text = logic.generate_ingredients_text(produkt, lang=lang)
    # Strip percentage annotations for the declared-composition display
    ingredients_text_pdf = re.sub(r'\s*\(\d+(?:\.\d+)?%\)', '', ingredients_text) if ingredients_text else ''
    # For EN: translate any remaining Polish ingredient names using the master dict
    if lang == "en":
        ingredients_text_pdf = _translate_any_text(ingredients_text_pdf)
    ingredients_text_pdf = _bold_allergens_html(ingredients_text_pdf, lang=lang)
    ingredient_origins = logic.get_ingredient_origins(produkt)

    # Parse certs
    certs = []
    try:
        certs = json.loads(produkt.certyfikaty or "[]")
    except:
        pass

    # Path to logo
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "..", "frontend", "src", "assets", "logo.png")
    if not os.path.exists(logo_path):
        logo_path = ""

    # Product image
    product_image_html = ""
    if produkt.image_url:
        img_relative = produkt.image_url.lstrip("/")
        img_abs_path = os.path.join(base_dir, img_relative).replace("\\", "/")
        if os.path.exists(img_abs_path):
            img_uri = "file:///" + img_abs_path
            product_image_html = f'<div style="text-align: center; margin-top: 15pt; margin-bottom: 15pt;"><img src="{img_uri}" style="max-width: 200pt; max-height: 200pt;"></div>'

    _register_fonts()

    # Allergen rows
    allergen_rows = "".join([
        f'<tr class="data-row">'
        f'<td style="width: 75%; word-wrap: break-word;">'
        f'{allergen_pdf_map.get(alg, ALLERGEN_MAP_PL.get(alg, alg.replace("_", " ").capitalize()))}'
        f'</td>'
        f'<td style="width: 25%;" class="allergen-status-{_status_to_css_class(status)}">'
        f'{_translate_status(status, lang)}'
        f'</td></tr>'
        for alg, status in allergens.items()
    ])

    # Ingredient origins rows – translate ingredient names for EN
    def _origin_name(name: str) -> str:
        if lang == "en":
            return _translate_any_text(name)
        return name

    origin_rows = "".join([
        f'<tr class="data-row">'
        f'<td>{_origin_name(item["name"])}</td>'
        f'<td style="text-align: center;">{str(round(item["percent"], 1) if item["percent"] >= 1 else round(item["percent"], 2)).replace(".", ",")}%</td>'
        f'<td>{", ".join(_translate_countries(item["countries"], lang)) if item["countries"] else "-"}</td>'
        f'</tr>'
        for item in ingredient_origins
    ])

    html_content = f"""
    <!DOCTYPE html>
    <html lang="{lang}" xmlns:pdf="http://www.w3.org/1999/xhtml">
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: a4 portrait;
                margin: 1cm 1.5cm 2.5cm 1.5cm;
                @frame footer_frame {{
                    -pdf-frame-content: footer_content;
                    left: 1.5cm;
                    width: 18cm;
                    bottom: 1cm;
                    height: 1.5cm;
                }}
            }}
            body {{
                font-family: Arial;
                font-size: 10pt;
                color: #333;
                line-height: 1.4;
            }}
            .header {{
                width: 100%;
                border-bottom: 0.5pt solid #ccc;
                padding-bottom: 5pt;
                margin-bottom: 15pt;
            }}
            .header-table {{
                width: 100%;
            }}
            .logo-cell {{
                width: 30%;
                vertical-align: middle;
            }}
            .company-info-cell {{
                width: 70%;
                text-align: right;
                vertical-align: middle;
                font-size: 8pt;
                color: #666;
            }}
            .title {{
                text-align: center;
                font-size: 18pt;
                font-weight: bold;
                text-transform: uppercase;
                margin-top: 20pt;
                margin-bottom: 5pt;
            }}
            .subtitle-cell {{
                text-align: center;
                font-size: 14pt;
                font-weight: bold;
                white-space: normal;
                word-wrap: break-word;
                overflow-wrap: break-word;
                overflow: visible;
            }}
            .divider {{
                border-bottom: 0.5pt solid #ccc;
                margin-bottom: 15pt;
            }}
            .indent-block {{
                width: 100%;
                margin-bottom: 20pt;
            }}
            .label {{
                font-weight: bold;
                color: #555;
            }}
            .section-header {{
                font-size: 14pt;
                font-weight: bold;
                border-bottom: 0.5pt solid #ccc;
                margin-top: 25pt;
                margin-bottom: 15pt;
                padding-bottom: 2pt;
                text-transform: uppercase;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15pt;
            }}
            th {{
                text-align: left;
                font-size: 9pt;
                color: #888;
                text-transform: uppercase;
                border-bottom: 0.5pt solid #eee;
                padding: 5pt 0;
            }}
            td {{
                padding: 5pt 0;
                vertical-align: top;
            }}
            .data-row td {{
                border-bottom: 0.2pt solid #f0f0f0;
            }}
            .no-border tr td {{
                border: none;
            }}
            .grey-bg {{
                background-color: #f9f9f9;
                padding: 10pt;
                margin-bottom: 15pt;
            }}
            .footer {{
                font-size: 8pt;
                color: #999;
                border-top: 0.5pt solid #ccc;
                padding-top: 5pt;
            }}
            .spacer {{
                height: 20pt;
            }}
            .allergen-status-Zawiera {{
                font-weight: bold;
            }}
            .allergen-status-contains {{
                font-weight: bold;
            }}
            .allergen-status-may-contain {{
                font-weight: bold;
                color: #555;
            }}
            .allergen-status-other {{
                font-weight: normal;
            }}
        </style>
    </head>
    <body>

        <!-- HEADER -->
        <div class="header">
            <table class="header-table">
                <tr>
                    <td class="logo-cell">
                        { f'<img src="{logo_path}" width="100">' if logo_path else 'LOGO' }
                    </td>
                    <td class="company-info-cell">
                        {COMPANY_INFO['name']}<br>
                        {COMPANY_INFO['address'].replace(', ', '<br>')}
                        {'<br>NIP: ' + COMPANY_INFO['nip'] if COMPANY_INFO['nip'] else ''}
                        {'<br>' + COMPANY_INFO['www'] + (' / ' + COMPANY_INFO['email'] if COMPANY_INFO['email'] else '') if COMPANY_INFO['www'] else ('<br>' + COMPANY_INFO['email'] if COMPANY_INFO['email'] else '')}
                    </td>
                </tr>
            </table>
        </div>

        <div class="title">{_s('SPECYFIKACJA WYROBU')}</div>
        <table style="width: 100%; table-layout: fixed; border-collapse: collapse; margin-bottom: 15pt;">
            <tr><td class="subtitle-cell">{product_name}</td></tr>
        </table>
        {product_image_html}
        <div class="divider"></div>

        <!-- SEKCJA 1: DANE OGÓLNE -->
        <div class="section-header">1. {_s('DANE OGÓLNE')}</div>

        <table class="no-border" style="margin-bottom: 15pt;">
            <tr><td class="label" style="width: 35%;">{_f('Kod produktu / ID')}:</td><td>{produkt.internal_id or (produkt.ean[-6:] if produkt.ean else '-')}</td></tr>
            <tr><td class="label">{_f('Data utworzenia')}:</td><td>{datetime.now().strftime('%d.%m.%Y')}</td></tr>
            <tr><td class="label">{_f('Kod EAN sztuki')}:</td><td>{produkt.ean or '-'}</td></tr>
            <tr><td class="label">{_f('Kod EAN kartonu')}:</td><td>{produkt.ean_karton or '-'}</td></tr>
            <tr><td class="label">CN:</td><td>{produkt.kod_cn or '-'}</td></tr>
            <tr><td class="label">PKWiU:</td><td>{produkt.kod_pkwiu or '-'}</td></tr>
            <tr><td class="label">{_f('Certyfikat (nazwa)')}:</td><td>{certs[0].get('rodzaj', '-') if certs else '-'}</td></tr>
            <tr><td class="label">{_f('COID certyfikatu')}:</td><td>{certs[0].get('coid', '-') if certs else '-'}</td></tr>
            <tr><td class="label">{_f('Data ważności certyfikatu')}:</td><td>{certs[0].get('data_waznosci', '-') if certs else '-'}</td></tr>
        </table>

        <div class="label" style="margin-bottom: 5pt;">{_f('Nazwa prawna / opis produktu')}:</div>
        <div style="margin-bottom: 15pt;">{legal_name or ('No description.' if lang == 'en' else 'Brak opisu.')}</div>

        <!-- SEKCJA 2: RECEPTURA -->
        <div class="section-header">2. {_s('RECEPTURA')}</div>

        <div class="label" style="margin-bottom: 5pt;">{_f('Skład deklarowany')}:</div>
        <div class="grey-bg">
            {ingredients_text_pdf or '-'}
        </div>

        <div class="label" style="margin-bottom: 5pt;">{_f('Składniki + kraje pochodzenia')}:</div>
        <table>
            <thead>
                <tr>
                    <th>{_f('Składnik')}</th>
                    <th style="text-align: center;">%</th>
                    <th>{_f('Kraj')}</th>
                </tr>
            </thead>
            <tbody>
                {origin_rows}
            </tbody>
        </table>

        <div class="label" style="margin-bottom: 5pt;">{_f('Alergeny')}:</div>
        <table style="margin-bottom: 15pt;">
            <thead>
                <tr>
                    <th style="width: 75%;">{_f('Alergen (pełna nazwa)')}</th>
                    <th style="width: 25%;">{_f('Zawartość')}</th>
                </tr>
            </thead>
            <tbody>
                {allergen_rows}
            </tbody>
        </table>

        <div class="label" style="margin-bottom: 5pt;">{_n('Wartości odżywcze (w 100 g)')}:</div>
        <table style="width: 250pt;">
            <thead>
                <tr>
                    <th>{_f('Wartość')}</th>
                    <th style="text-align: right;">100 g</th>
                </tr>
            </thead>
            <tbody>
                <tr class="data-row"><td>{_n('Wartość energetyczna')}</td><td style="text-align: right;">{int(round(nutrition['energia_kj'], 0))} kJ / {int(round(nutrition['energia_kcal'], 0))} kcal</td></tr>
                <tr class="data-row"><td>{_n('Tłuszcz')}</td><td style="text-align: right;">{int(round(nutrition['tluszcz'], 0))} g</td></tr>
                <tr class="data-row"><td>{_n('- w tym kwasy tłuszczowe nasycone')}</td><td style="text-align: right;">{int(round(nutrition['kwasy_nasycone'], 0))} g</td></tr>
                <tr class="data-row"><td>{_n('Węglowodany')}</td><td style="text-align: right;">{int(round(nutrition['weglowodany'], 0))} g</td></tr>
                <tr class="data-row"><td>{_n('- w tym cukry')}</td><td style="text-align: right;">{int(round(nutrition['cukry'], 0))} g</td></tr>
                <tr class="data-row"><td>{_n('Białko')}</td><td style="text-align: right;">{str(round(nutrition['bialko'], 1)).replace(".", ",")} g</td></tr>
                <tr class="data-row"><td>{_n('Sól')}</td><td style="text-align: right;">{str(round(nutrition['sol'], 2)).replace(".", ",")} g</td></tr>
            </tbody>
        </table>

        <!-- SEKCJA 3: LOGISTYKA -->
        <div class="section-header">3. {_s('LOGISTYKA')}</div>

        <div class="label" style="margin-bottom: 5pt;">{_f('Wymiary')}:</div>
        <table>
            <thead>
                <tr>
                    <th>{_f('Poziom')}</th>
                    <th style="text-align: center;">{_f('Wysokość [cm]')}</th>
                    <th style="text-align: center;">{_f('Szerokość [cm]')}</th>
                    <th style="text-align: center;">{_f('Głębokość [cm]')}</th>
                </tr>
            </thead>
            <tbody>
                <tr class="data-row"><td>{_f('Produkt solo')}</td><td style="text-align: center;">{produkt.logistyka_wymiary_solo_h}</td><td style="text-align: center;">{produkt.logistyka_wymiary_solo_w}</td><td style="text-align: center;">{produkt.logistyka_wymiary_solo_d}</td></tr>
                <tr class="data-row"><td>{_f('W opakowaniu jednostkowym')}</td><td style="text-align: center;">{produkt.logistyka_wymiary_jednostka_h}</td><td style="text-align: center;">{produkt.logistyka_wymiary_jednostka_w}</td><td style="text-align: center;">{produkt.logistyka_wymiary_jednostka_d}</td></tr>
                <tr class="data-row"><td>{_f('Opakowanie zbiorcze 1°')}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze1_h}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze1_w}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze1_d}</td></tr>
                <tr class="data-row"><td>{_f('Opakowanie zbiorcze 2°')}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze2_h}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze2_w}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze2_d}</td></tr>
                <tr class="data-row"><td>{_f('Opakowanie zbiorcze 3°')}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze3_h}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze3_w}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze3_d}</td></tr>
            </tbody>
        </table>

        <div class="label" style="margin-bottom: 5pt;">{_f('Wagi')}:</div>
        <table style="margin-bottom: 15pt;">
            <thead>
                <tr>
                    <th style="width: 50%;">{_f('Parametr')}</th>
                    <th style="width: 50%;">{_f('Wartość')}</th>
                </tr>
            </thead>
            <tbody>
                <tr class="data-row"><td style="width: 50%;">{_f('Waga netto sztuki')}</td><td style="width: 50%;">{str(produkt.logistyka_waga_netto_szt).replace(".", ",")} kg</td></tr>
                <tr class="data-row"><td style="width: 50%;">{_f('Waga brutto sztuki')}</td><td style="width: 50%;">{str(produkt.logistyka_waga_brutto_szt).replace(".", ",")} kg</td></tr>
                <tr class="data-row"><td style="width: 50%;">{_f('Waga netto zbiorcze')}</td><td style="width: 50%;">{str(produkt.logistyka_waga_netto_zbiorcze).replace(".", ",")} kg</td></tr>
                <tr class="data-row"><td style="width: 50%;">{_f('Waga brutto zbiorcze')}</td><td style="width: 50%;">{str(produkt.logistyka_waga_brutto_zbiorcze).replace(".", ",")} kg</td></tr>
            </tbody>
        </table>

        <div class="label" style="margin-bottom: 5pt;">{_f('Paletyzacja')}:</div>
        <table style="margin-bottom: 8pt;">
            <thead>
                <tr>
                    <th style="width: 50%;">{_f('Parametr')}</th>
                    <th style="width: 50%;">{_f('Wartość')}</th>
                </tr>
            </thead>
            <tbody>
                <tr class="data-row"><td style="width: 50%;">{_f('Ilość sztuk produktu w opakowaniu zbiorczym [szt]')}</td><td style="width: 50%;">{produkt.logistyka_sztuk_w_zbiorczym}</td></tr>
                <tr class="data-row"><td style="width: 50%;">{_f('Ilość kartonów na warstwie [szt]')}</td><td style="width: 50%;">{produkt.logistyka_kartonow_na_warstwie}</td></tr>
                <tr class="data-row"><td style="width: 50%;">{_f('Ilość warstw na palecie [szt]')}</td><td style="width: 50%;">{produkt.logistyka_warstw_na_palecie}</td></tr>
                <tr class="data-row"><td style="width: 50%;">{_f('Ilość kartonów na palecie [szt]')}</td><td style="width: 50%;">{produkt.logistyka_kartonow_na_palecie}</td></tr>
                <tr class="data-row"><td style="width: 50%;">{_f('Ilość sztuk na warstwie palety [szt]')}</td><td style="width: 50%;">{produkt.logistyka_sztuk_na_warstwie}</td></tr>
                <tr class="data-row"><td style="width: 50%;">{_f('Ilość sztuk na palecie [szt]')}</td><td style="width: 50%;">{produkt.logistyka_sztuk_na_palecie}</td></tr>
                <tr class="data-row"><td style="width: 50%;">{_f('Wysokość palety z nośnikiem [cm]')}</td><td style="width: 50%;">{int(produkt.logistyka_wysokosc_palety) if produkt.logistyka_wysokosc_palety is not None else '-'}</td></tr>
            </tbody>
        </table>
        <div style="margin-bottom: 15pt;">{_f('Rodzaj palety')}: {produkt.logistyka_rodzaj_palety or '-'}</div>

        <!-- SEKCJA 4: ORGANOLEPTYKA -->
        <div class="section-header">4. {_s('ORGANOLEPTYKA')}</div>

        <div style="margin-bottom: 15pt;">
            <div class="label" style="margin-top: 5pt;">{_f('Smak')}</div>
            <div>{_orga(produkt.organoleptyka_smak, 'organoleptyka_smak') or '-'}</div>
            <div class="label" style="margin-top: 5pt;">{_f('Zapach')}</div>
            <div>{_orga(produkt.organoleptyka_zapach, 'organoleptyka_zapach') or '-'}</div>
            <div class="label" style="margin-top: 5pt;">{_f('Kolor')}</div>
            <div>{_orga(produkt.organoleptyka_kolor, 'organoleptyka_kolor') or '-'}</div>
            <div class="label" style="margin-top: 5pt;">{_f('Wygląd zewnętrzny')}</div>
            <div>{_orga(produkt.organoleptyka_wyglad_zewnetrzny, 'organoleptyka_wyglad_zewnetrzny') or '-'}</div>
            <div class="label" style="margin-top: 5pt;">{_f('Wygląd na przekroju')}</div>
            <div>{_orga(produkt.organoleptyka_wyglad_na_przekroju, 'organoleptyka_wyglad_na_przekroju') or '-'}</div>
        </div>

        <!-- SEKCJA 5: INNE -->
        <div class="section-header">5. {_s('INNE')}</div>

        <div class="label" style="margin-top: 10pt; margin-bottom: 5pt;">{_f('Warunki przechowywania')}:</div>
        <div style="margin-bottom: 15pt;">{_orga(produkt.warunki_przechowywania, 'warunki_przechowywania') or '-'}</div>

        <div class="label" style="margin-top: 10pt; margin-bottom: 5pt;">{_f('Termin przydatności')}:</div>
        <div style="margin-bottom: 15pt;">{_orga(produkt.termin_przydatnosci, 'termin_przydatnosci') or '-'}</div>

        <div class="label" style="margin-top: 10pt; margin-bottom: 5pt;">{_f('Wyrażenie i format')}:</div>
        <div style="margin-bottom: 15pt;">{_orga(produkt.wyrazenie_format_daty, 'wyrazenie_format_daty') or '-'}</div>

        <div class="label" style="margin-top: 10pt; margin-bottom: 5pt;">{_f('Informacje dodatkowe')}:</div>
        <div style="margin-bottom: 15pt;">{_orga(produkt.informacje_dodatkowe, 'informacje_dodatkowe') or '-'}</div>

        <!-- FOOTER CONTENT -->
        <div id="footer_content" class="footer">
            <table class="no-border" style="width: 100%;">
                <tr>
                    <td style="width: 33%;">{COMPANY_INFO['name']}</td>
                    <td style="width: 34%; text-align: center;">{COMPANY_INFO['address']}</td>
                    <td style="width: 33%; text-align: right;">
                        {page_label} <pdf:pagenumber/> {of_label} <pdf:pagecount/>
                    </td>
                </tr>
            </table>
        </div>

    </body>
    </html>
    """

    result = BytesIO()
    pisa.CreatePDF(html_content, dest=result, encoding='utf-8', link_callback=_link_callback)
    result.seek(0)
    return result
