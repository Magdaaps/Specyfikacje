$ErrorActionPreference = "Stop"
try {
    # Find the file dynamically to avoid encoding issues in hardcoded path
    $file = Get-ChildItem -Path . -Filter "*Wszystkie surowce*.xlsx" | Select-Object -First 1
    if (-not $file) {
        Write-Error "Could not find the Excel file."
        exit 1
    }
    $excelPath = $file.FullName
    Write-Host "Analyzing: $excelPath"

    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false

    $workbook = $excel.Workbooks.Open($excelPath)
    
    foreach ($sheet in $workbook.Sheets) {
        Write-Host "SHEET: $($sheet.Name)"
        
        # Read header row (first row)
        $usedCols = $sheet.UsedRange.Columns.Count
        if ($usedCols -gt 50) { $usedCols = 50 } # Limit for display
        
        $headers = @()
        for ($col = 1; $col -le $usedCols; $col++) {
            $val = $sheet.Cells.Item(1, $col).Text # Use Text to get formatted value
            $headers += "'$val'"
        }
        
        Write-Host "HEADERS: $($headers -join ', ')"
        
        # Peek at data (row 2)
        $row2 = @()
        for ($col = 1; $col -le 5; $col++) {
            $val = $sheet.Cells.Item(2, $col).Text
            $row2 += "'$val'"
        }
        Write-Host "SAMPLE: $($row2 -join ', ')"
        Write-Host "---"
    }

    $workbook.Close($false)
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
    Write-Host "Done."
}
catch {
    Write-Error "Error: $_"
    if ($excel) { $excel.Quit() }
}
