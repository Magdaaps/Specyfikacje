# process_product_data.ps1
# Replicating VBA logic for CSV files using only ASCII in the script source.

Add-Type -AssemblyName "Microsoft.VisualBasic"

function Normalize-Key($s) {
    if ($null -eq $s) { return "" }
    [string]$t = "$s"
    # Replace non-breaking space (160) and zero-width spaces
    $t = $t.Replace([string][char]160, " ")
    $t = $t.Replace([string][char]8203, "")
    $t = $t.Replace("`t", " ").Trim()
    
    while ($t -match "  ") { $t = $t.Replace("  ", " ") }
    
    $t = $t.ToLower()
    
    # Polish diacritics removal using Unicode codes
    $map = @{
        [char]0x0105 = 'a'; [char]0x0107 = 'c'; [char]0x0119 = 'e'; [char]0x0142 = 'l'; [char]0x0144 = 'n'
        [char]0x00F3 = 'o'; [char]0x015B = 's'; [char]0x017A = 'z'; [char]0x017C = 'z'
        [char]0x0104 = 'a'; [char]0x0106 = 'c'; [char]0x0118 = 'e'; [char]0x0141 = 'l'; [char]0x0143 = 'n'
        [char]0x00D3 = 'o'; [char]0x015A = 's'; [char]0x0179 = 'z'; [char]0x017B = 'z'
    }
    foreach ($k in $map.Keys) {
        $t = $t.Replace([string]$k, [string]$map[$k])
    }
    
    # Remove all non-alphanumeric
    $t = $t -replace "[^a-z0-9]", ""
    return $t
}

function Normalize-Status($txt) {
    if ($null -eq $txt -or $txt -eq "") { return "Nie zawiera" }
    $t = "$txt".ToLower().Trim()
    
    # Define Polish terms using Unicode to avoid mangling
    $moze = "mo" + [char]0x017C + "e"
    $sladowe = [char]0x015B + "ladowe"
    
    if ($t -match "zawiera|tak|yes|1|contains") {
        if ($t -match "$moze|sladowe|slad|may") {
            return "Moze zawiera" + [char]0x0107
        }
        return "Zawiera"
    }
    elseif ($t -eq "" -or $t -match "nie zawiera|brak|-|0|nie|no") {
        return "Nie zawiera"
    }
    else {
        return "Moze zawiera" + [char]0x0107
    }
}

function Combine-Status($curr, $incoming) {
    if ($curr -match "Zawiera" -or $incoming -match "Zawiera") { return "Zawiera" }
    if ($curr -match "Moze" -or $incoming -match "Moze") { return "Moze zawiera" + [char]0x0107 }
    return "Nie zawiera"
}

function Get-CsvRows($path) {
    $parser = [Microsoft.VisualBasic.FileIO.TextFieldParser]::new($path)
    $parser.SetDelimiters(",")
    $parser.HasFieldsEnclosedInQuotes = $true
    $rows = New-Object System.Collections.Generic.List[string[]]
    while (-not $parser.EndOfData) {
        $rows.Add($parser.ReadFields())
    }
    $parser.Close()
    return $rows
}

# --- DATA LOADING ---
Write-Host "Loading data..."
$surowceRows = Get-CsvRows "Surowce.csv"
$produktyRows = Get-CsvRows "Produkty.csv"

$surowceLookup = @{}
for ($i = 1; $i -lt $surowceRows.Count; $i++) {
    $name = $surowceRows[$i][1]
    if ($name) { 
        $key = Normalize-Key $name
        if (-not $surowceLookup.ContainsKey($key)) {
            $surowceLookup[$key] = $surowceRows[$i]
        }
    }
}

$prodHeaders = $produktyRows[0]

# --- PROCESSING ---
Write-Host "Processing products..."
for ($r = 1; $r -lt $produktyRows.Count; $r++) {
    $rowP = $produktyRows[$r]
    if ($rowP.Count -lt 2 -or -not $rowP[1]) { continue }
    
    Write-Host "Product: $($rowP[1])"
    
    $aggregatedAllergens = @("Nie zawiera") * 14
    $ingredients = @()
    
    # Ingredient columns: 3 to 35
    for ($c = 3; $c -le 35; $c++) {
        if ($c -ge $rowP.Count) { break }
        $vStr = $rowP[$c] -replace ",", "."
        if ($vStr -as [double]) {
            $v = [double]$vStr
            if ($v -gt 0) {
                $ingName = $prodHeaders[$c]
                $ingKey = Normalize-Key $ingName
                $surRow = $null
                
                if ($surowceLookup.ContainsKey($ingKey)) { $surRow = $surowceLookup[$ingKey] }
                else {
                    # Try partial match if no exact match
                    foreach ($k in $surowceLookup.Keys) {
                        if ($ingKey.Contains($k) -or $k.Contains($ingKey)) { $surRow = $surowceLookup[$k]; break }
                    }
                }
                
                if ($surRow) {
                    # Allergens: 39-52
                    for ($a = 0; $a -lt 14; $a++) {
                        if ((39 + $a) -lt $surRow.Count) {
                            $status = Normalize-Status $surRow[39 + $a]
                            $aggregatedAllergens[$a] = Combine-Status $aggregatedAllergens[$a] $status
                        }
                    }
                    # Origin (93-114)
                    for ($oc = 93; $oc -le 114; $oc++) {
                        if ($oc -lt $rowP.Count -and $oc -lt $prodHeaders.Count) {
                            if ((Normalize-Key $prodHeaders[$oc]) -eq $ingKey) {
                                if (53 -lt $surRow.Count) { $rowP[$oc] = $surRow[53] }
                            }
                        }
                    }
                    $ingredients += [PSCustomObject]@{ Name = $ingName; Val = $v }
                }
            }
        }
    }
    
    # Update Allergens (115-128)
    for ($a = 0; $a -lt 14; $a++) { 
        if ((115 + $a) -lt $rowP.Count) { $rowP[115 + $a] = $aggregatedAllergens[$a] } 
    }
    
    # Sklad generation
    $skladParts = $ingredients | Sort-Object Val -Descending | ForEach-Object { $_.Name }
    $finalSklad = $skladParts -join ", "
    if (91 -lt $rowP.Count) { $rowP[91] = $finalSklad }
    if (92 -lt $rowP.Count) { $rowP[92] = $finalSklad }
}

# --- EXPORT ---
Write-Host "Exporting..."
$sw = [System.IO.StreamWriter]::new("Produkty_updated.csv", $false, [System.Text.Encoding]::UTF8)
$sw.Write([char]65279)
foreach ($row in $produktyRows) {
    if ($row.Count -eq 0) { continue }
    $line = ($row | ForEach-Object { 
            $v = if ($null -eq $_) { "" } else { "$_" }
            if ($v -match "[,`n`r]") { "`"$($v -replace '\"','\"\"')`"" } else { $v }
        }) -join ","
    $sw.WriteLine($line)
}
$sw.Close()
Write-Host "Done! Saved to Produkty_updated.csv"
