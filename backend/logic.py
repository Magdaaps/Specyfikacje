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
    # key: normalized (lowercase), value: [display_name, total_percent]
    total_ingredients = {}

    def _t(name):
        """Translate ingredient name when lang=en and translate_fn provided."""
        if lang == "en" and translate_fn:
            return translate_fn(name)
        return name

    def _add(name, contribution):
        key = name.lower().strip()
        if key in total_ingredients:
            prev_display, prev_total = total_ingredients[key]
            display = name if contribution > prev_total else prev_display
            total_ingredients[key] = [display, prev_total + contribution]
        else:
            total_ingredients[key] = [name, contribution]

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
                        percent = float(item.get('procent', 0))
                        if percent <= 0:
                            continue
                        name = _t(name)
                        contribution = (percent / 100.0) * raw_material_percent
                        _add(name, contribution)
                        ingredients_found = True
            except (json.JSONDecodeError, ValueError):
                pass

        if not ingredients_found:
            # Fallback to raw material name if no percentage breakdown is available
            if lang == "en":
                name = s.surowiec.nazwa_en or _t(s.surowiec.nazwa)
            else:
                name = s.surowiec.nazwa
            _add(name, raw_material_percent)

    # Sort ingredients by percentage descending (stable sort preserves insertion order for ties)
    sorted_ingredients = sorted(
        ((display, total) for display, total in total_ingredients.values()),
        key=lambda x: x[1], reverse=True
    )

    # Group entries that share a "prefix: identifier" pattern (e.g. multiple barwnik: Exx)
    prefix_groups = {}  # prefix -> [(identifier, percent)]  — preserves sorted order
    ungrouped = []      # [(name, percent)]

    def _fmt_pct(p):
        if p >= 0.01:   return f'{p:.2f}'
        if p >= 0.001:  return f'{p:.3f}'
        if p >= 0.0001: return f'{p:.4f}'
        if p > 0:       return f'{p:.5f}'
        return '0'

    for name, percent in sorted_ingredients:
        if percent <= 0:
            continue
        if ': ' in name:
            prefix, identifier = name.split(': ', 1)
            if prefix not in prefix_groups:
                prefix_groups[prefix] = []
            prefix_groups[prefix].append((identifier, percent))
        else:
            ungrouped.append((name, percent))

    # Build final parts: (display_str, sort_key, use_semicolon_after)
    final_parts = []

    for name, percent in ungrouped:
        final_parts.append((f"{name} ({_fmt_pct(percent)}%)", percent, False))

    for prefix, items in prefix_groups.items():
        combined_percent = sum(p for _, p in items)
        ids_str = ', '.join(id_ for id_, _ in items)
        use_semi = len(items) > 1
        final_parts.append((f"{prefix}: {ids_str} ({_fmt_pct(combined_percent)}%)", combined_percent, use_semi))

    # Sort final parts by combined percent descending
    final_parts.sort(key=lambda x: x[1], reverse=True)

    # Build output string with ; after grouped additive categories, , elsewhere
    result = []
    for i, (display, _, use_semi) in enumerate(final_parts):
        is_last = (i == len(final_parts) - 1)
        result.append(display)
        if not is_last:
            result.append('; ' if use_semi else ', ')
        elif use_semi:
            result.append(';')

    return ''.join(result)

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

        use_fallback = True
        if sklad_list and len(sklad_list) > 0:
            for item in sklad_list:
                pl_name = item.get('nazwa', '').strip()
                if not pl_name: continue
                percent = float(item.get('procent', 0))
                if percent <= 0: continue
                display_name = _t(pl_name)
                contribution = (percent / 100.0) * raw_material_percent
                use_fallback = False

                if display_name not in aggregation:
                    aggregation[display_name] = {"percent": 0.0, "countries": set()}

                aggregation[display_name]["percent"] += contribution

                # Countries are keyed by PL name in origins_dict
                countries = origins_dict.get(pl_name, [])
                for c in countries:
                    aggregation[display_name]["countries"].add(c)

        if use_fallback:
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

    # Convert to sorted list, excluding items with 0 contribution
    result = []
    for name, data in aggregation.items():
        pct = round(data["percent"], 6)
        if pct <= 0:
            continue
        result.append({
            "name": name,
            "percent": pct,
            "countries": sorted(list(data["countries"]))
        })

    result.sort(key=lambda x: x["percent"], reverse=True)
    return result

