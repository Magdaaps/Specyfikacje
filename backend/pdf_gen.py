from xhtml2pdf import pisa
from io import BytesIO
import logic
import models
import json
import os
from datetime import datetime

# Company Info (Placeholders as per requirements)
COMPANY_INFO = {
    "name": "ANTIGRAVITY FOOD SP. Z O.O.",
    "address": "ul. Kosmiczna 42, 00-001 Warszawa",
    "nip": "123-456-78-90",
    "www": "www.antigravity-food.pl",
    "email": "biuro@antigravity-food.pl"
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

def generate_pdf(produkt: models.Produkt):
    # Prepare data
    nutrition = logic.calculate_nutrition(produkt)
    allergens = logic.aggregate_allergens(produkt)
    ingredients_text = logic.generate_ingredients_text(produkt, lang="pl")
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

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: a4 portrait;
                margin: 2cm 1.5cm 2.5cm 1.5cm;
                @frame footer_frame {{
                    -pdf-frame-content: footer_content;
                    left: 1.5cm;
                    width: 18cm;
                    bottom: 1cm;
                    height: 1.5cm;
                }}
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
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
                font-weight: semi-bold;
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
            .page-number::after {{
                content: counter(page);
            }}
            .total-pages::after {{
                content: counter(pages);
            }}
            .spacer {{
                height: 20pt;
            }}
            .allergen-status-Zawiera {{
                font-weight: bold;
            }}
            .allergen-status-Może {{
                font-weight: semi-bold;
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
                        {COMPANY_INFO['address']}<br>
                        NIP: {COMPANY_INFO['nip']}<br>
                        {COMPANY_INFO['www']} / {COMPANY_INFO['email']}
                    </td>
                </tr>
            </table>
        </div>

        <div class="title">SPECYFIKACJA WYROBU</div>
        <div class="subtitle">{produkt.nazwa_pl}</div>
        <div class="divider"></div>

        <!-- IDENTIFICATION BLOCK -->
        <table class="indent-block no-border">
            <tr>
                <td style="width: 50%;">
                    <table class="no-border">
                        <tr><td class="label" style="width: 40%;">Kod produktu / ID:</td><td>{produkt.internal_id or produkt.ean[-6:] if produkt.ean else '-'}</td></tr>
                        <tr><td class="label">EAN:</td><td>{produkt.ean or '-'}</td></tr>
                        <tr><td class="label">CN:</td><td>{produkt.kod_cn or '-'}</td></tr>
                        <tr><td class="label">PKWiU:</td><td>{produkt.kod_pkwiu or '-'}</td></tr>
                    </table>
                </td>
                <td style="width: 50%;">
                    <table class="no-border">
                        <tr><td class="label" style="width: 40%;">Data utworzenia:</td><td>{datetime.now().strftime('%d.%m.%Y')}</td></tr>
                        <tr><td class="label">Data aktualizacji:</td><td>{produkt.updated_at.strftime('%d.%m.%Y') if produkt.updated_at else '-'}</td></tr>
                        <tr><td class="label">Certyfikat:</td><td>{certs[0].get('rodzaj', '-') if certs else '-'}</td></tr>
                        <tr><td class="label">Ważność cert.:</td><td>{certs[0].get('data_waznosci', '-') if certs else '-'}</td></tr>
                    </table>
                </td>
            </tr>
        </table>

        <!-- SEKCJA 1: DANE OGÓLNE -->
        <div class="section-header">1. DANE OGÓLNE</div>
        
        <div class="label" style="margin-bottom: 5pt;">Nazwa prawna / opis produktu:</div>
        <div style="margin-bottom: 15pt;">{produkt.prawna_nazwa_pl or 'Brak opisu.'}</div>

        <div class="label" style="margin-bottom: 5pt;">Skład surowcowy:</div>
        <table>
            <thead>
                <tr>
                    <th>Surowiec</th>
                    <th style="text-align: right;">%</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f'<tr class="data-row"><td>{s.surowiec.nazwa}</td><td style="text-align: right;">{str(s.procent).replace(".", ",")}%</td></tr>' for s in produkt.skladniki])}
            </tbody>
        </table>

        <!-- SEKCJA 2: RECEPTURA -->
        <div class="section-header">2. RECEPTURA</div>
        
        <div class="label" style="margin-bottom: 5pt;">Skład deklarowany:</div>
        <div class="grey-bg">
            {ingredients_text or '-'}
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
                {"".join([f'<tr class="data-row"><td>{item["name"]}</td><td style="text-align: center;">{str(round(item["percent"], 2)).replace(".", ",")}%</td><td>{", ".join(item["countries"]) if item["countries"] else "-"}</td></tr>' for item in ingredient_origins])}
            </tbody>
        </table>

        <div class="label" style="margin-bottom: 5pt;">Alergeny:</div>
        <div style="margin-bottom: 15pt;">
            {"<br>".join([f'<span>{ALLERGEN_MAP_PL.get(alg, alg.replace("_", " ").capitalize())} – <span class="allergen-status-{status[:7].strip()}">{status}</span></span>' for alg, status in allergens.items()])}
        </div>

        <div class="label" style="margin-bottom: 5pt;">Wartości odżywcze (w 100 g):</div>
        <table style="width: 250pt;">
            <thead>
                <tr>
                    <th>Wartość</th>
                    <th style="text-align: right;">100 g</th>
                </tr>
            </thead>
            <tbody>
                <tr class="data-row"><td>Wartość energetyczna</td><td style="text-align: right;">{round(nutrition['energia_kj'], 0)} kJ / {round(nutrition['energia_kcal'], 0)} kcal</td></tr>
                <tr class="data-row"><td>Tłuszcz</td><td style="text-align: right;">{str(round(nutrition['tluszcz'], 1)).replace(".", ",")} g</td></tr>
                <tr class="data-row"><td>- w tym kwasy tłuszczowe nasycone</td><td style="text-align: right;">{str(round(nutrition['kwasy_nasycone'], 1)).replace(".", ",")} g</td></tr>
                <tr class="data-row"><td>Węglowodany</td><td style="text-align: right;">{str(round(nutrition['weglowodany'], 1)).replace(".", ",")} g</td></tr>
                <tr class="data-row"><td>- w tym cukry</td><td style="text-align: right;">{str(round(nutrition['cukry'], 1)).replace(".", ",")} g</td></tr>
                <tr class="data-row"><td>Białko</td><td style="text-align: right;">{str(round(nutrition['bialko'], 1)).replace(".", ",")} g</td></tr>
                <tr class="data-row"><td>Sól</td><td style="text-align: right;">{str(round(nutrition['sol'], 2)).replace(".", ",")} g</td></tr>
                <tr class="data-row"><td>Błonnik</td><td style="text-align: right;">{str(round(nutrition['blonnik'], 1)).replace(".", ",")} g</td></tr>
            </tbody>
        </table>

        <!-- SEKCJA 3: LOGISTYKA -->
        <div class="section-header">3. LOGISTYKA</div>

        <div class="label" style="margin-bottom: 5pt;">Wymiary:</div>
        <table>
            <thead>
                <tr>
                    <th>Poziom</th>
                    <th style="text-align: center;">H [cm]</th>
                    <th style="text-align: center;">W [cm]</th>
                    <th style="text-align: center;">D [cm]</th>
                </tr>
            </thead>
            <tbody>
                <tr class="data-row"><td>Jednostka solo</td><td style="text-align: center;">{produkt.logistyka_wymiary_solo_h}</td><td style="text-align: center;">{produkt.logistyka_wymiary_solo_w}</td><td style="text-align: center;">{produkt.logistyka_wymiary_solo_d}</td></tr>
                <tr class="data-row"><td>Opak. zbiorcze</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze1_h}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze1_w}</td><td style="text-align: center;">{produkt.logistyka_wymiary_zbiorcze1_d}</td></tr>
                <tr class="data-row"><td>Wysokość palety</td><td style="text-align: center;">{produkt.logistyka_wysokosc_palety}</td><td style="text-align: center;">-</td><td style="text-align: center;">-</td></tr>
            </tbody>
        </table>

        <div class="label" style="margin-bottom: 5pt;">Wagi:</div>
        <div style="margin-bottom: 15pt;">
            Waga netto sztuki: {str(produkt.logistyka_waga_netto_szt).replace(".", ",")} kg<br>
            Waga brutto sztuki: {str(produkt.logistyka_waga_brutto_szt).replace(".", ",")} kg<br>
            Waga netto zbiorcze: {str(produkt.logistyka_waga_netto_zbiorcze).replace(".", ",")} kg<br>
            Waga brutto zbiorcze: {str(produkt.logistyka_waga_brutto_zbiorcze).replace(".", ",")} kg
        </div>

        <div class="label" style="margin-bottom: 5pt;">Paletyzacja:</div>
        <table class="no-border">
            <tr>
                <td>
                    Sztuk w zbiorczym: {produkt.logistyka_sztuk_w_zbiorczym}<br>
                    Kartonów na warstwie: {produkt.logistyka_kartonow_na_warstwie}<br>
                    Warstw na palecie: {produkt.logistyka_warstw_na_palecie}
                </td>
                <td>
                    Kartonów na palecie: {produkt.logistyka_kartonow_na_palecie}<br>
                    Sztuk na palecie: {produkt.logistyka_sztuk_na_palecie}<br>
                    Rodzaj palety: {produkt.logistyka_rodzaj_palety or '-'}
                </td>
            </tr>
        </table>

        <!-- SEKCJA 4: INNE -->
        <div class="section-header">4. INNE</div>

        <div class="label">Organoleptyka:</div>
        <div style="margin-bottom: 10pt;">
            <div class="label" style="font-size: 9pt; margin-top: 5pt;">Smak</div>
            <div>{produkt.organoleptyka_smak or '-'}</div>
            <div class="label" style="font-size: 9pt; margin-top: 5pt;">Zapach</div>
            <div>{produkt.organoleptyka_zapach or '-'}</div>
            <div class="label" style="font-size: 9pt; margin-top: 5pt;">Kolor</div>
            <div>{produkt.organoleptyka_kolor or '-'}</div>
            <div class="label" style="font-size: 9pt; margin-top: 5pt;">Wygląd zewnętrzny</div>
            <div>{produkt.organoleptyka_wyglad_zewnetrzny or '-'}</div>
            <div class="label" style="font-size: 9pt; margin-top: 5pt;">Wygląd na przekroju</div>
            <div>{produkt.organoleptyka_wyglad_na_przekroju or '-'}</div>
        </div>

        <div class="label" style="margin-top: 10pt;">Warunki przechowywania:</div>
        <div>{produkt.warunki_przechowywania or '-'}</div>

        <div class="label" style="margin-top: 10pt;">Termin przydatności:</div>
        <div>{produkt.termin_przydatnosci or '-'}</div>

        <div class="label" style="margin-top: 10pt;">Wyrażenie i format:</div>
        <div>{produkt.wyrazenie_format_daty or '-'}</div>

        <div class="label" style="margin-top: 10pt;">Informacje dodatkowe:</div>
        <div>{produkt.informacje_dodatkowe or '-'}</div>

        <!-- FOOTER CONTENT -->
        <div id="footer_content" class="footer">
            <table class="no-border" style="width: 100%;">
                <tr>
                    <td style="width: 33%;">{COMPANY_INFO['name']}</td>
                    <td style="width: 34%; text-align: center;">{COMPANY_INFO['address']}</td>
                    <td style="width: 33%; text-align: right;">
                        Strona <span class="page-number"></span> z <span class="total-pages"></span><br>
                        Wygenerowano: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                    </td>
                </tr>
            </table>
        </div>

    </body>
    </html>
    """

    result = BytesIO()
    pisa.CreatePDF(html_content, dest=result, encoding='utf-8')
    result.seek(0)
    return result
