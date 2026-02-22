Add-Type -AssemblyName "Microsoft.VisualBasic"
function Get-Headers($path) {
    $parser = [Microsoft.VisualBasic.FileIO.TextFieldParser]::new($path)
    $parser.SetDelimiters(",")
    $parser.HasFieldsEnclosedInQuotes = $true
    return $parser.ReadFields()
}

$hP = Get-Headers "Produkty.csv"
Write-Host "--- Produkty.csv ---"
for ($i = 0; $i -lt $hP.Count; $i++) {
    if ($hP[$i] -match "ProductID|Nazwa produktu|Skład|Gluten") {
        Write-Host "$i : $($hP[$i])"
    }
}
# Also find boundaries of ingredients
# Ingredients start after 'waga (g)' (index 2)
# And end before 'barwnik' (index 30?)
Write-Host "--- Ingredients in Produkty.csv ---"
Write-Host "Start: $(3) Label: $($hP[3])"
for ($i = 3; $i -lt $hP.Count; $i++) {
    if ($hP[$i] -match "barwnik") {
        Write-Host "End before: $i Label: $($hP[$i])"
        break
    }
}
