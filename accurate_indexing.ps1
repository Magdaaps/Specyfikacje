Add-Type -AssemblyName "Microsoft.VisualBasic"
function Get-Headers($path) {
    $parser = [Microsoft.VisualBasic.FileIO.TextFieldParser]::new($path)
    $parser.SetDelimiters(",")
    $parser.HasFieldsEnclosedInQuotes = $true
    return $parser.ReadFields()
}

$hS = Get-Headers "Surowce.csv"
Write-Host "--- Surowce.csv ---"
for ($i = 0; $i -lt $hS.Count; $i++) {
    if ($hS[$i] -match "Gluten|Mięczaki|Cukier\.1|Origin|Kraj") {
        Write-Host "$i : $($hS[$i])"
    }
}

$hP = Get-Headers "Produkty.csv"
Write-Host "--- Produkty.csv ---"
for ($i = 0; $i -lt $hP.Count; $i++) {
    if ($hP[$i] -match "Gluten|Mięczaki|Cukier\.1|Skład|Country") {
        Write-Host "$i : $($hP[$i])"
    }
}
