Add-Type -AssemblyName "Microsoft.VisualBasic"
function Get-Headers($path) {
    $parser = [Microsoft.VisualBasic.FileIO.TextFieldParser]::new($path)
    $parser.SetDelimiters(",")
    $parser.HasFieldsEnclosedInQuotes = $true
    return $parser.ReadFields()
}

$hP = Get-Headers "Produkty.csv"
for ($i = 90; $i -lt 115; $i++) {
    Write-Host "$i : $($hP[$i])"
}
