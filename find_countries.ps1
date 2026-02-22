$line = Get-Content "Surowce.csv" -TotalCount 2 | Select-Object -Last 1
# Split by comma but respect quotes
$matches = [regex]::Matches($line, '(?:^|,)(?:"(?<val>[^"]*)"|(?<val>[^,]*))')
$i = 0
foreach ($m in $matches) {
    if ($m.Groups['val'].Value -like "*Francja*" -or $m.Groups['val'].Value -like "*Brazylia*") {
        Write-Host "Found countries at index $i : $($m.Groups['val'].Value)"
    }
    $i++
}
