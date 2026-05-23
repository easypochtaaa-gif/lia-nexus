# 👁‍🗨 STAB WIFI SURVEILLANCE NODE
Write-Host "--- SYSTEM ACTIVE: MONITORING WIRELESS ETHER ---" -ForegroundColor Cyan
$old_scan = ""

while ($true) {
    $current_scan = netsh wlan show networks mode=bssid | Out-String
    
    if ($current_scan -ne $old_scan) {
        Clear-Host
        Write-Host "--- [SCAN UPDATE: $(Get-Date -Format 'HH:mm:ss')] ---" -ForegroundColor Green
        
        # Фильтруем вывод, чтобы видеть только важные детали
        $lines = $current_scan -split "`n"
        foreach ($line in $lines) {
            if ($line -like "*SSID*" -or $line -like "*BSSID*" -or $line -like "*Сигнал*" -or $line -like "*Канал*") {
                if ($line -like "*BSSID 1*") {
                    Write-Host $line -ForegroundColor Yellow
                } else {
                    Write-Host $line
                }
            }
        }
        $old_scan = $current_scan
    }
    
    Start-Sleep -Seconds 5
}
