import sqlite3
import json
import os

db_path = os.path.join(os.getcwd(), "product_generator.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

data = [
    {
        "nazwa": "ZAFIRO WHITE - polewa mleczna",
        "sklad_pl": "cukier, całkowicie uwodorniony olej z ziaren palmy olejowej, 12-13% serwatka (z mleka) w proszku, 4-6% mleko pełne w proszku, emulgatory [<1% tristearynian sorbitolu (e 492), lecytyny słonecznikowej (e 322), mono- i diglicerydy kwasów tłuszczowych estryfikowane kwasem cytrynowym (e 472c)], aromat.",
        "sklad_procentowy": [
            {"nazwa": "cukier", "procent": 47.5},
            {"nazwa": "tłuszcz roślinny (olej palmowy)", "procent": 34.0},
            {"nazwa": "serwatka w proszku (z mleka)", "procent": 12.5},
            {"nazwa": "mleko pełne w proszku", "procent": 5.0},
            {"nazwa": "emulgator", "procent": 0.5},
            {"nazwa": "aromat", "procent": 0.25}
        ],
        "pochodzenie_skladnikow": [
            {"nazwa": "cukier", "kraje": "Francja, Dominikana, Holandia, Belgia, Niemcy, Włochy"},
            {"nazwa": "tłuszcz roślinny (olej palmowy)", "kraje": "Indonezja, Malezja"},
            {"nazwa": "serwatka w proszku (z mleka)", "kraje": "Włochy, Hiszpania, Francja, Belgia, Portugalia"},
            {"nazwa": "mleko pełne w proszku", "kraje": "Unia Europejska (Niemcy, Austria, Belgia, Dania, Holandia)"},
            {"nazwa": "emulgator", "kraje": "Indonezja, Malezja"},
            {"nazwa": "aromat", "kraje": "Hiszpania"}
        ]
    },
    {
        "nazwa": "ZAFIRO MILK - polewa mleczno kakaowa",
        "sklad_pl": "cukier, całkowicie uwodorniony olej z ziaren palmy olejowej, serwatka (z mleka) w proszku, kakao w proszku o obniżonej zawartości tłuszczu, pełne mleko, w proszku, emulgatory: tristearynian sorbitolu (E492), lecytyny słonecznikowe (E322); aromat.",
        "sklad_procentowy": [
            {"nazwa": "cukier", "procent": 42.0},
            {"nazwa": "tłuszcz roślinny (olej palmowy)", "procent": 27.0},
            {"nazwa": "serwatka w proszku (z mleka)", "procent": 22.0},
            {"nazwa": "kakao", "procent": 4.0},
            {"nazwa": "mleko pełne", "procent": 3.0},
            {"nazwa": "emulgator", "procent": 0.5},
            {"nazwa": "aromat", "procent": 0.25}
        ],
        "pochodzenie_skladnikow": [
            {"nazwa": "cukier", "kraje": "Francja, Dominikana, Holandia, Belgia, Niemcy, Włochy"},
            {"nazwa": "tłuszcz roślinny (olej palmowy)", "kraje": "Indonezja, Malezja"},
            {"nazwa": "serwatka w proszku (z mleka)", "kraje": "Włochy, Hiszpania, Francja, Belgia, Portugalia"},
            {"nazwa": "kakao", "kraje": "Wybrzeże Kości Słoniowej, Ghana, Nigeria, Kamerun"},
            {"nazwa": "mleko pełne", "kraje": "Unia Europejska (Niemcy, Austria, Belgia, Dania, Holandia)"},
            {"nazwa": "emulgator", "kraje": "Indonezja, Malezja, Argentyna, Węgry, Turcja, Rosja, Ukraina"},
            {"nazwa": "aromat", "kraje": "Hiszpania, Francja"}
        ]
    }
]

for s in data:
    cur.execute("""
        UPDATE surowce 
        SET sklad_pl = ?, sklad_procentowy = ?, pochodzenie_skladnikow = ?
        WHERE nazwa = ?
    """, (s['sklad_pl'], json.dumps(s['sklad_procentowy']), json.dumps(s['pochodzenie_skladnikow']), s['nazwa']))

conn.commit()
conn.close()
print("Updated database with example data from images.")
