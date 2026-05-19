# tail_log.ps1 — Live pipeline log viewer
# Launched by run_scheduler.bat — closes automatically when pipeline completes

$logFile = "C:\ai-agents\ai-job-search-pipeline\logs\scheduler.log"
$doneMarker = "=== Daily pipeline complete"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Job Search Pipeline - Live Log" -ForegroundColor Cyan
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "  Waiting for pipeline to start..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

while (-not (Test-Path $logFile)) { Start-Sleep -Milliseconds 500 }

$lastCount = (Get-Content $logFile).Count

while ($true) {
    Start-Sleep -Milliseconds 500
    $lines = Get-Content $logFile
    $currentCount = $lines.Count

    if ($currentCount -gt $lastCount) {
        $newLines = $lines[$lastCount..($currentCount - 1)]
        foreach ($line in $newLines) {
            if ($line -match "ERROR|error|Error|FAIL|ABORT") {
                Write-Host $line -ForegroundColor Red
            } elseif ($line -match "Step [1-4]:|Generate Docs|Digest|Scout|Analyze") {
                Write-Host $line -ForegroundColor Cyan
            } elseif ($line -match "YES|8\.|9\.|10\.") {
                Write-Host $line -ForegroundColor Green
            } elseif ($line -match "MAYBE|7\.") {
                Write-Host $line -ForegroundColor Yellow
            } elseif ($line -match $doneMarker) {
                Write-Host $line -ForegroundColor Green
                Write-Host ""
                Write-Host "========================================" -ForegroundColor Green
                Write-Host "  Pipeline complete! Closing in 30s..." -ForegroundColor Green
                Write-Host "========================================" -ForegroundColor Green
                Start-Sleep -Seconds 30
                exit
            } else {
                Write-Host $line
            }
        }
        $lastCount = $currentCount
    }
}
