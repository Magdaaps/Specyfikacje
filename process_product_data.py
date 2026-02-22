import csv
import re
import unicodedata

def normalize_key(s):
    if not s:
        return ""
    # Strip diacritics
    s = "".join(c for c in unicodedata.normalize('NFD', str(s)) if unicodedata.category(c) != 'Mn')
    # Replace common Polish characters that might fail NFD (though most should work)
    mapping = {
        'ł': 'l', 'Ł': 'L'
    }
    for k, v in mapping.items():
        s = s.replace(k, v)
    
    s = s.lower()
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def normalize_status(txt):
    if not txt:
        return "Nie zawiera"
    t = str(txt).lower().strip()
    if any(word in t for word in ["zawiera", "tak", "yes", "1", "contains"]):
        if any(word in t for word in ["moze", "może", "sladowe", "śladowe", "slad", "ślad", "may"]):
            return "Może zawierać"
        return "Zawiera"
    elif not t or any(word in t for word in ["nie zawiera", "brak", "-", "0", "nie", "no"]):
        return "Nie zawiera"
    else:
        return "Może zawierać"

def combine_status(curr, incoming):
    if curr == "Zawiera" or incoming == "Zawiera":
        return "Zawiera"
    if curr == "Może zawierać" or incoming == "Może zawierać":
        return "Może zawierać"
    return "Nie zawiera"

def process():
    print("Loading data...")
    surowce = {}
    with open('Surowce.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers_s = next(reader)
        for row in reader:
            if len(row) > 1:
                name = row[1]
                surowce[normalize_key(name)] = row

    with open('Produkty.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers_p = next(reader)
        rows_p = list(reader)

    print("Processing products...")
    for row in rows_p:
        if not row or len(row) < 2 or not row[1]:
            continue
        
        product_name = row[1]
        print(f"  Product: {product_name}")
        
        aggregated_allergens = ["Nie zawiera"] * 14
        ingredients_info = []
        
        # Ingredient columns in Produkty.csv: Index 3 to 35
        for c in range(3, 36):
            if c >= len(row): break
            val_str = row[c].replace(',', '.')
            try:
                val = float(val_str)
            except ValueError:
                val = 0
                
            if val > 0:
                ing_name = headers_p[c]
                ing_key = normalize_key(ing_name)
                
                sur_row = surowce.get(ing_key)
                if not sur_row:
                    # Try partial match
                    for k in surowce:
                        if ing_key in k or k in ing_key:
                            sur_row = surowce[k]
                            break
                
                if sur_row:
                    # Allergens in Surowce.csv: 39 to 52
                    for i in range(14):
                        if 39 + i < len(sur_row):
                            status = normalize_status(sur_row[39 + i])
                            aggregated_allergens[i] = combine_status(aggregated_allergens[i], status)
                    
                    # Origin columns in Produkty.csv: 93 to 114
                    for oc in range(93, 115):
                        if oc < len(row) and oc < len(headers_p):
                            if normalize_key(headers_p[oc]) == ing_key:
                                if 53 < len(sur_row):
                                    row[oc] = sur_row[53] # Index 53 is Country (labeled Cukier.1)
                    
                    ingredients_info.append({
                        'name': ing_name,
                        'val': val
                    })
        
        # Update Allergens in Produkty.csv: 115 to 128
        for i in range(14):
            if 115 + i < len(row):
                row[115 + i] = aggregated_allergens[i]
        
        # Generate Sklad (91)
        if 91 < len(row):
            # Categorization
            main = []
            fruits = []
            emulsifiers = []
            colors = []
            aromas = []
            
            for ing in ingredients_info:
                name_l = ing['name'].lower()
                if "aromat" in name_l:
                    aromas.append(ing['name'])
                elif "emulgator" in name_l or "lecytyna" in name_l:
                    emulsifiers.append(ing['name'])
                elif "barwnik" in name_l:
                    colors.append(ing['name'])
                elif "liofiliz" in name_l:
                    fruits.append(ing)
                else:
                    main.append(ing)
            
            main.sort(key=lambda x: x['val'], reverse=True)
            fruits.sort(key=lambda x: x['val'], reverse=True)
            
            parts = []
            for m in main:
                parts.append(m['name'])
            
            if fruits:
                f_list = [f"{f['name']} ({f['val']}%)" for f in fruits]
                parts.append("owoce liofilizowane: " + ", ".join(f_list))
            
            if emulsifiers:
                pref = "emulgator: " if len(emulsifiers) == 1 else "emulgatory: "
                parts.append(pref + ", ".join(emulsifiers))
                
            if colors:
                parts.append("barwniki: " + ", ".join(colors))
                
            if aromas:
                parts.append(", ".join(aromas))
            
            final_sklad = ", ".join(parts)
            row[91] = final_sklad
            if 92 < len(row):
                row[92] = final_sklad

    print("Saving results...")
    with open('Produkty_updated.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers_p)
        writer.writerows(rows_p)
    print("Done! Saved to Produkty_updated.csv")

if __name__ == "__main__":
    process()
