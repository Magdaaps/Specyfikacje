from xhtml2pdf import pisa, default as pisa_default
from io import BytesIO
import logic
import models
import json
import os
import re
import unicodedata
from datetime import datetime
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


def _status_to_css_class(status: str) -> str:
    normalized = unicodedata.normalize("NFKD", status or "")
    normalized = normalized.encode("ascii", "ignore").decode("ascii").lower()
    if "zawiera" in normalized:
        return "contains"
    if "moze" in normalized and "zawier" in normalized:
        return "may-contain"
    return "other"


FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"


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
# Allergen auto-bolding
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


def _bold_allergens_html(text: str) -> str:
    """Wrap allergen words in <strong> tags (input is plain text, output is HTML)."""
    if not text:
        return text
    return _ALLERGEN_PATTERN_PDF.sub(r"<strong>\1</strong>", text)


def _link_callback(uri, rel):
    """Resolve file:/// URIs so xhtml2pdf can read local images."""
    if uri.startswith("file:///"):
        return uri[8:]
    return uri


def generate_pdf(produkt: models.Produkt):
    # Prepare data
    nutrition = logic.calculate_nutrition(produkt)
    allergens = logic.aggregate_allergens(produkt)
    ingredients_text = logic.generate_ingredients_text(produkt, lang="pl")
    ingredients_text_pdf = re.sub(r'\s*\(\d+(?:\.\d+)?%\)', '', ingredients_text) if ingredients_text else ''
    ingredients_text_pdf = _bold_allergens_html(ingredients_text_pdf)
    ingredient_origins = logic.get_ingredient_origins(produkt)
    
    # Parse certs
    certs = []
    try:
        certs = json.loads(produkt.certyfikaty or "[]")
    except:
        pass
    
    # Path to logo - trying to find it
    # We assume backend is run from the backend directory.
    # Frontend assets are in ../frontend/src/assets/logo.png
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "..", "frontend", "src", "assets", "logo.png")
    if not os.path.exists(logo_path):
        logo_path = "" # Fallback if not found

    # Product image
    product_image_html = ""
    if produkt.image_url:
        img_relative = produkt.image_url.lstrip("/")  # e.g. "uploads/filename.jpg"
        img_abs_path = os.path.join(base_dir, img_relative).replace("\\", "/")
        if os.path.exists(img_abs_path):
            img_uri = "file:///" + img_abs_path
            product_image_html = f'<div style="text-align: center; margin-top: 15pt; margin-bottom: 15pt;"><img src="{img_uri}" style="max-width: 200pt; max-height: 200pt;"></div>'

    _register_fonts()

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pl" xmlns:pdf="http://www.w3.org/1999/xhtml">
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
            .subtitle {{
                text-align: center;
                font-size: 14pt;
                font-weight: bold;
                margin-bottom: 15pt;
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

        <div class="title">SPECYFIKACJA WYROBU</div>
        <div class="subtitle">{produkt.nazwa_pl}</div>
        {product_image_html}
        <div class="divider"></div>

        <!-- SEKCJA 1: DANE OGÓLNE -->
        <div class="section-header">1. DANE OGÓLNE</div>

        <table class="no-border" style="margin-bottom: 15pt;">
            <tr><td class="label" style="width: 35%;">Kod produktu / ID:</td><td>{produkt.internal_id or (produkt.ean[-6:] if produkt.ean else '-')}</td></tr>
            <tr><td class="label">Data utworzenia:</td><td>{datetime.now().strftime('%d.%m.%Y')}</td></tr>
            <tr><td class="label">Kod EAN sztuki:</td><td>{produkt.ean or '-'}</td></tr>
            <tr><td class="label">Kod EAN kartonu:</td><td>{produkt.ean_karton or '-'}</td></tr>
            <tr><td class="label">CN:</td><td>{produkt.kod_cn or '-'}</td></tr>
            <tr><td class="label">PKWiU:</td><td>{produkt.kod_pkwiu or '-'}</td></tr>
            <tr><td class="label">Certyfikat (nazwa):</td><td>{certs[0].get('rodzaj', '-') if certs else '-'}</td></tr>
            <tr><td class="label">COID certyfikatu:</td><td>{certs[0].get('coid', '-') if certs else '-'}</td></tr>
            <tr><td class="label">Data ważności certyfikatu:</td><td>{certs[0].get('data_waznosci', '-') if certs else '-'}</td></tr>
        </table>

        <div class="label" style="margin-bottom: 5pt;">Nazwa prawna / opis produktu:</div>
        <div style="margin-bottom: 15pt;">{produkt.prawna_nazwa_pl or 'Brak opisu.'}</div>

        <!-- SEKCJA 2: RECEPTURA -->
        <div class="section-header">2. RECEPTURA</div>
        
        <div class="label" style="margin-bottom: 5pt;">Skład deklarowany:</div>
        <div class="grey-bg">
            {ingredients_text_pdf or '-'}
        </div>

        <div class="label" style="margin-bottom: 5pt;">Składniki + kraje pochodzenia:</div>
        <table>
            <thead>
                <tr>
                    <th>Składnik</th>
                    <th style="text-align: center;">%</th>
                    <th>Kraj</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f'<tr class="data-row"><td>{item["name"]}</td><td style="text-align: center;">{str(round(item["percent"], 1) if item["percent"] >= 1 else round(item["percent"], 2)).replace(".", ",")}%</td><td>{", ".join(item["countries"]) if item["countries"] else "-"}</td></tr>' for item in ingredient_origins])}
            </tbody>
        </table>

        <div class="label" style="margin-bottom: 5pt;">Alergeny:</div>
        <table style="margin-bottom: 15pt;">
            <thead>
                <tr>
                    <th style="width: 75%;">Alergen (pełna nazwa)</th>
                    <th style="width: 25%;">Zawartość</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f'<tr class="data-row"><td style="width: 75%; word-wrap: break-word;">{ALLERGEN_MAP_PDF.get(alg, ALLERGEN_MAP_PL.get(alg, alg.replace("_", " ").capitalize()))}</td><td style="width: 25%;" class="allergen-status-{_status_to_css_class(status)}">{status}</td></tr>' for alg, status in allergens.items()])}
            </tbody>
        </table>

        <div class="label" style="margin-bottom: 5pt;">Wartości odżywcze (w 100 g):</div>
        <table style="width: 250pt;">
            <thead>
                <tr>
                    <th>Wartość</th>
                    <th style="text-align: right;">100 g</th>
                </tr>
            </thead>
            <tbody>
                <tr class="data-row"><td>Wartość energetyczna</td><td style="text-align: right;">{int(round(nutrition['energia_kj'], 0))} kJ / {int(round(nutrition['energia_kcal'], 0))} kcal</td></tr>
                <tr class="data-row"><td>Tłuszcz</td><td style="text-align: right;">{int(round(nutrition['tluszcz'], 0))} g</td></tr>
                <tr class="data-row"><td>- w tym kwasy tłuszczowe nasycone</td><td style="text-align: right;">{int(round(nutrition['kwasy_nasycone'], 0))} g</td></tr>
                <tr class="data-row"><td>Węglowodany</td><td style="text-align: right;">{int(round(nutrition['weglowodany'], 0))} g</td></tr>
                <tr class="data-row"><td>- w tym cukry</td><td style="text-align: right;">{int(round(nutrition['cukry'], 0))} g</td></tr>
                <tr class="data-row"><td>Białko</td><td style="text-align: right;">{str(round(nutrition['bialko'], 1)).replace(".", ",")} g</td></tr>
                <tr class="data-row"><td>Sól</td><td style="text-align: right;">{str(round(nutrition['sol'], 2)).replace(".", ",")} g</td></tr>
            </tbody>
        </table>

        <!-- SEKCJA 3: LOGISTYKA -->
        <div class="section-header">3. LOGISTYKA</div>

        <div class="label" style="margin-bottom: 5pt;">Wymiary:</div>
        <table>
            <thead>
                <tr>
                    <th>Poziom</th>
                    <th style="text-align: center;">Wysokość [cm]</th>
                    <th style="text-align: center;">Szerokość [cm]</th>
                    <th style="text-align: center;">Głębokość [cm]</th>
                </tr>
            </thead>
            <tbody>
                <tr class="data-row"><td>Produkt solo</td><td style="text-align: center;">{produkt.logistyka_wymiary_solo_h}</td><td style="text-align: center;">{produkt.logistyka_wymiary_solo_w}</td><td style="text-align: center;">{produkt.logistyka_wymiary_solo_d}</td></tr>
                <tr class="data-row"><td>W opakowaniu jednostkowym</td><td style="text-align: center;">{produkt.logistyka_wymiary_jednostka_h}</td><td style="text-align: center;">{produkt.logistyka_wymiary_jednostka_w}</td><td style="text-align: center;">{produkt.logistyka_wymiary_jednostka_d}</td></tr>
                <tr class="data-row"><td>Opakowanie zbiorcze 1°</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze1_h}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze1_w}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze1_d}</td></tr>
                <tr class="data-row"><td>Opakowanie zbiorcze 2°</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze2_h}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze2_w}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze2_d}</td></tr>
                <tr class="data-row"><td>Opakowanie zbiorcze 3°</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze3_h}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze3_w}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze3_d}</td></tr>
            </tbody>
        </table>

        <div class="label" style="margin-bottom: 5pt;">Wagi:</div>
        <table style="margin-bottom: 15pt;">
            <thead>
                <tr>
                    <th style="width: 50%;">Parametr</th>
                    <th style="width: 50%;">Wartość</th>
                </tr>
            </thead>
            <tbody>
                <tr class="data-row"><td style="width: 50%;">Waga netto sztuki</td><td style="width: 50%;">{str(produkt.logistyka_waga_netto_szt).replace(".", ",")} kg</td></tr>
                <tr class="data-row"><td style="width: 50%;">Waga brutto sztuki</td><td style="width: 50%;">{str(produkt.logistyka_waga_brutto_szt).replace(".", ",")} kg</td></tr>
                <tr class="data-row"><td style="width: 50%;">Waga netto zbiorcze</td><td style="width: 50%;">{str(produkt.logistyka_waga_netto_zbiorcze).replace(".", ",")} kg</td></tr>
                <tr class="data-row"><td style="width: 50%;">Waga brutto zbiorcze</td><td style="width: 50%;">{str(produkt.logistyka_waga_brutto_zbiorcze).replace(".", ",")} kg</td></tr>
            </tbody>
        </table>

        <div class="label" style="margin-bottom: 5pt;">Paletyzacja:</div>
        <table style="margin-bottom: 8pt;">
            <thead>
                <tr>
                    <th style="width: 50%;">Parametr</th>
                    <th style="width: 50%;">Wartość</th>
                </tr>
            </thead>
            <tbody>
                <tr class="data-row"><td style="width: 50%;">Ilość sztuk produktu w opakowaniu zbiorczym [szt]</td><td style="width: 50%;">{produkt.logistyka_sztuk_w_zbiorczym}</td></tr>
                <tr class="data-row"><td style="width: 50%;">Ilość kartonów na warstwie [szt]</td><td style="width: 50%;">{produkt.logistyka_kartonow_na_warstwie}</td></tr>
                <tr class="data-row"><td style="width: 50%;">Ilość warstw na palecie [szt]</td><td style="width: 50%;">{produkt.logistyka_warstw_na_palecie}</td></tr>
                <tr class="data-row"><td style="width: 50%;">Ilość kartonów na palecie [szt]</td><td style="width: 50%;">{produkt.logistyka_kartonow_na_palecie}</td></tr>
                <tr class="data-row"><td style="width: 50%;">Ilość sztuk na warstwie palety [szt]</td><td style="width: 50%;">{produkt.logistyka_sztuk_na_warstwie}</td></tr>
                <tr class="data-row"><td style="width: 50%;">Ilość sztuk na palecie [szt]</td><td style="width: 50%;">{produkt.logistyka_sztuk_na_palecie}</td></tr>
                <tr class="data-row"><td style="width: 50%;">Wysokość palety z nośnikiem [cm]</td><td style="width: 50%;">{int(produkt.logistyka_wysokosc_palety) if produkt.logistyka_wysokosc_palety is not None else '-'}</td></tr>
            </tbody>
        </table>
        <div style="margin-bottom: 15pt;">Rodzaj palety: {produkt.logistyka_rodzaj_palety or '-'}</div>

        <!-- SEKCJA 4: ORGANOLEPTYKA -->
        <div class="section-header">4. ORGANOLEPTYKA</div>

        <div style="margin-bottom: 15pt;">
            <div class="label" style="margin-top: 5pt;">Smak</div>
            <div>{produkt.organoleptyka_smak or '-'}</div>
            <div class="label" style="margin-top: 5pt;">Zapach</div>
            <div>{produkt.organoleptyka_zapach or '-'}</div>
            <div class="label" style="margin-top: 5pt;">Kolor</div>
            <div>{produkt.organoleptyka_kolor or '-'}</div>
            <div class="label" style="margin-top: 5pt;">Wygląd zewnętrzny</div>
            <div>{produkt.organoleptyka_wyglad_zewnetrzny or '-'}</div>
            <div class="label" style="margin-top: 5pt;">Wygląd na przekroju</div>
            <div>{produkt.organoleptyka_wyglad_na_przekroju or '-'}</div>
        </div>

        <!-- SEKCJA 5: INNE -->
        <div class="section-header">5. INNE</div>

        <div class="label" style="margin-top: 10pt; margin-bottom: 5pt;">Warunki przechowywania:</div>
        <div style="margin-bottom: 15pt;">{produkt.warunki_przechowywania or '-'}</div>

        <div class="label" style="margin-top: 10pt; margin-bottom: 5pt;">Termin przydatności:</div>
        <div style="margin-bottom: 15pt;">{produkt.termin_przydatnosci or '-'}</div>

        <div class="label" style="margin-top: 10pt; margin-bottom: 5pt;">Wyrażenie i format:</div>
        <div style="margin-bottom: 15pt;">{produkt.wyrazenie_format_daty or '-'}</div>

        <div class="label" style="margin-top: 10pt; margin-bottom: 5pt;">Informacje dodatkowe:</div>
        <div style="margin-bottom: 15pt;">{produkt.informacje_dodatkowe or '-'}</div>

        <!-- FOOTER CONTENT -->
        <div id="footer_content" class="footer">
            <table class="no-border" style="width: 100%;">
                <tr>
                    <td style="width: 33%;">{COMPANY_INFO['name']}</td>
                    <td style="width: 34%; text-align: center;">{COMPANY_INFO['address']}</td>
                    <td style="width: 33%; text-align: right;">
                        Strona <pdf:pagenumber/> z <pdf:pagecount/>
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

