$csvPath = "Surowce.csv"
$content = Get-Content $csvPath -First 1
$headers = $content -split ','
for ($i = 0; $i -lt $headers.Count; $i++) {
    Write-Host "$i : $($headers[$i])"
}
