Add-Type -AssemblyName "Microsoft.VisualBasic"
$content = Get-Content "Produkty.csv" -First 1
$headers = [Microsoft.VisualBasic.FileIO.TextFieldParser]::new((New-Object System.IO.StringReader($content)))
$headers.SetDelimiters(",")
$hArray = $headers.ReadFields()
for ($i = 0; $i -lt $hArray.Count; $i++) {
    Write-Host "$i : $($hArray[$i])"
}
