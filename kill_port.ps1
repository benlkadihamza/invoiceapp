$connections = Get-NetTCPConnection -LocalPort 5000 -State Listen
foreach ($conn in $connections) {
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Host "Killed PID $($conn.OwningProcess)"
}
Start-Sleep -Seconds 1
$remaining = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue
if (-not $remaining) { Write-Host "Port 5000 is free" }
