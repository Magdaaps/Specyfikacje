$csv = Import-Csv "Surowce.csv"
$headers = $csv[0].PSObject.Properties.Name
for ($i = 0; $i -lt $headers.Count; $i++) {
    Write-Host "$i : $($headers[$i])"
}
