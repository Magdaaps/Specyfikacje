$excelPath = "c:\Users\MonikaBrawiak\Documents\Generator kart produktów 2.0\BAZA_SUROWCÓW - Wszystkie surowce - najnowszy od Marzeny.xlsx"
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false

try {
    $workbook = $excel.Workbooks.Open($excelPath)
    Write-Host "File: $excelPath"
    
    foreach ($sheet in $workbook.Sheets) {
        Write-Host "Sheet: $($sheet.Name)"
        
        # Read header row (first row)
        $headerRow = $sheet.UsedRange.Rows.Item(1)
        $headers = @()
        
        # Iterate cells in first row until empty (limit to 50 columns to be safe)
        for ($col = 1; $col -le 50; $col++) {
            $val = $sheet.Cells.Item(1, $col).Value2
            if ([string]::IsNullOrWhiteSpace($val)) {
                # Try checking a bit further if there are gaps, but usually headers are contiguous
                # Actually, UsedRange should give us the extent.
                # Let's rely on UsedRange columns count for upper bound but stop empty.
            }
            if ($null -ne $val) {
                $headers += $val
            }
        }
        
        # Better approach using UsedRange
        $usedCols = $sheet.UsedRange.Columns.Count
        $headers = @()
        if ($usedCols -gt 0) {
            $range = $sheet.Range($sheet.Cells.Item(1, 1), $sheet.Cells.Item(1, $usedCols))
            if ($usedCols -eq 1) {
                 $headers += $range.Value2
            } else {
                # Value2 returns 2D array for ranges
                $values = $range.Value2
                # In PS, accessing 2D array from COM can be tricky.
                # Let's simple iterate.
                for ($col = 1; $col -le $usedCols; $col++) {
                     $val = $sheet.Cells.Item(1, $col).Value2
                     if ($null -ne $val) {
                        $headers += $val
                     }
                }
            }
        }
        
        Write-Host "Headers: $($headers -join ', ')"
        
        # Peek at data (row 2)
        $row2 = @()
        for ($col = 1; $col -le 5; $col++) {
             $val = $sheet.Cells.Item(2, $col).Value2
             if ($null -ne $val) { $row2 += $val }
        }
        Write-Host "Sample Data (Row 2, first 5 cols): $($row2 -join ', ')"
        Write-Host "----------------"
    }
}
catch {
    Write-Error "Error processing file: $_"
}
finally {
    if ($workbook) { $workbook.Close($false) }
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
}
