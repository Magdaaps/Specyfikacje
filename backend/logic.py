import json
import models

def calculate_nutrition(produkt: models.Produkt):
    nutrition = {
        "energia_kj": 0.0,
        "energia_kcal": 0.0,
        "tluszcz": 0.0,
        "kwasy_nasycone": 0.0,
        "weglowodany": 0.0,
        "cukry": 0.0,
        "bialko": 0.0,
        "sol": 0.0,
        "blonnik": 0.0
    }
    
    total_percent = sum(s.procent for s in produkt.skladniki)
    if total_percent == 0:
        return nutrition
        
    for s in produkt.skladniki:
        if not s.surowiec:
            continue
            
        factor = (s.procent or 0.0) / 100.0
        nutrition["energia_kj"] += (s.surowiec.energia_kj or 0.0) * factor
        nutrition["energia_kcal"] += (s.surowiec.energia_kcal or 0.0) * factor
        nutrition["tluszcz"] += (s.surowiec.tluszcz or 0.0) * factor
        nutrition["kwasy_nasycone"] += (s.surowiec.kwasy_nasycone or 0.0) * factor
        nutrition["weglowodany"] += (s.surowiec.weglowodany or 0.0) * factor
        nutrition["cukry"] += (s.surowiec.cukry or 0.0) * factor
        nutrition["bialko"] += (s.surowiec.bialko or 0.0) * factor
        nutrition["sol"] += (s.surowiec.sol or 0.0) * factor
        nutrition["blonnik"] += (s.surowiec.blonnik or 0.0) * factor
        
    return nutrition

def aggregate_allergens(produkt: models.Produkt):
    fields = [
        "gluten", "skorupiaki", "jaja", "ryby", "orzeszki_ziemne", "soja", 
        "mleko", "orzechy", "seler", "gorczyca", "sezam", "dwutlenek_siarki", 
        "lubin", "mieczaki"
    ]
    
    allergens = {field: "Nie zawiera" for field in fields}
    
    def combine(current, incoming):
        if current == "Zawiera" or incoming == "Zawiera":
            return "Zawiera"
        if current == "Może zawierać" or incoming == "Może zawierać":
            return "Może zawierać"
        return "Nie zawiera"

    for s in produkt.skladniki:
        sur = s.surowiec
        if not sur:
            continue
        for field in fields:
            val = getattr(sur, f"alergen_{field}")
            allergens[field] = combine(allergens[field], val)
            
    return allergens

def generate_ingredients_text(produkt: models.Produkt, lang="pl", translate_fn=None):
    total_ingredients = {}

    def _t(name):
        """Translate ingredient name when lang=en and translate_fn provided."""
        if lang == "en" and translate_fn:
            return translate_fn(name)
        return name

    for s in produkt.skladniki:
        raw_material_percent = s.procent
        sklad_json = s.surowiec.sklad_procentowy

        ingredients_found = False
        if sklad_json:
            try:
                sklad_list = json.loads(sklad_json)
                if isinstance(sklad_list, list) and len(sklad_list) > 0:
                    for item in sklad_list:
                        name = item.get('nazwa', '').strip()
                        if not name:
                            continue
                        name = _t(name)
                        percent = float(item.get('procent', 0))
                        contribution = (percent / 100.0) * raw_material_percent

                        total_ingredients[name] = total_ingredients.get(name, 0) + contribution
                        ingredients_found = True
            except (json.JSONDecodeError, ValueError):
                pass

        if not ingredients_found:
            # Fallback to raw material name if no percentage breakdown is available
            if lang == "en":
                name = s.surowiec.nazwa_en or _t(s.surowiec.nazwa)
            else:
                name = s.surowiec.nazwa
            total_ingredients[name] = total_ingredients.get(name, 0) + raw_material_percent

    # Sort ingredients by percentage descending
    sorted_ingredients = sorted(total_ingredients.items(), key=lambda x: x[1], reverse=True)
    
    parts = []
    for name, percent in sorted_ingredients:
        if percent > 0:
            parts.append(f"{name} ({round(percent, 2)}%)")
        
    return ", ".join(parts)

def get_ingredient_origins(produkt: models.Produkt, translate_fn=None):
    aggregation = {} # { name: { "percent": sum, "countries": set } }

    def _t(name):
        if translate_fn:
            return translate_fn(name)
        return name

    for s in produkt.skladniki:
        if not s.surowiec:
            continue

        raw_material_percent = s.procent or 0.0
        sklad_json = s.surowiec.sklad_procentowy
        origins_json = s.surowiec.pochodzenie_skladnikow

        # Load composition and origins
        sklad_list = []
        if sklad_json:
            try:
                sklad_list = json.loads(sklad_json)
            except:
                pass

        origins_dict = {} # { ingredient_name_pl: [countries] }
        if origins_json:
            try:
                origins_list = json.loads(origins_json)
                for item in origins_list:
                    name = item.get('nazwa', '').strip()
                    kraje_raw = item.get('kraje', '')
                    kraje = []
                    if isinstance(kraje_raw, str):
                         kraje = [k.strip() for k in kraje_raw.split(',') if k.strip()]
                    elif isinstance(kraje_raw, list):
                         kraje = [str(k).strip() for k in kraje_raw if str(k).strip()]
                    if name:
                        origins_dict[name] = kraje
            except:
                pass

        if sklad_list and len(sklad_list) > 0:
            for item in sklad_list:
                pl_name = item.get('nazwa', '').strip()
                if not pl_name: continue
                display_name = _t(pl_name)
                percent = float(item.get('procent', 0))
                contribution = (percent / 100.0) * raw_material_percent

                if display_name not in aggregation:
                    aggregation[display_name] = {"percent": 0.0, "countries": set()}

                aggregation[display_name]["percent"] += contribution

                # Countries are keyed by PL name in origins_dict
                countries = origins_dict.get(pl_name, [])
                for c in countries:
                    aggregation[display_name]["countries"].add(c)
        else:
            # Fallback to raw material name
            pl_name = s.surowiec.nazwa
            display_name = _t(pl_name)
            if display_name not in aggregation:
                aggregation[display_name] = {"percent": 0.0, "countries": set()}
            aggregation[display_name]["percent"] += raw_material_percent

            if s.surowiec.kraj_pochodzenia:
                kraje = [k.strip() for k in s.surowiec.kraj_pochodzenia.split(',') if k.strip()]
                for c in kraje:
                    aggregation[display_name]["countries"].add(c)

    # Convert to sorted list
    result = []
    for name, data in aggregation.items():
        result.append({
            "name": name,
            "percent": round(data["percent"], 4), # Higher precision for sorting, display will round to 2
            "countries": sorted(list(data["countries"]))
        })
    
    result.sort(key=lambda x: x["percent"], reverse=True)
    return result

