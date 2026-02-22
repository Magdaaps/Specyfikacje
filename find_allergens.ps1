$line = Get-Content "Surowce.csv" -TotalCount 2 | Select-Object -Last 1
$matches = [regex]::Matches($line, '(?:^|,)(?:"(?<val>[^"]*)"|(?<val>[^,]*))')
$i = 0
foreach ($m in $matches) {
    $v = $m.Groups['val'].Value
    if ($v -eq "zawiera" -or $v -eq "może zawierać" -or $v -eq "nie zawiera") {
        Write-Host "$i : $v"
    }
    $i++
}
