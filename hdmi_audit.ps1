# 👁‍🗨 STAB HDMI & DISPLAY AUDIT
Write-Host "--- STARTING HARDWARE PROBE: HDMI/DISPLAY ---" -ForegroundColor Cyan

# 1. Получаем список всех мониторов из WMI
$monitors = Get-WmiObject -Namespace "root\wmi" -Class WmiMonitorID

if ($monitors) {
    foreach ($m in $monitors) {
        $name = [System.Text.Encoding]::ASCII.GetString($m.UserFriendlyName -ne 0)
        $serial = [System.Text.Encoding]::ASCII.GetString($m.SerialNumberID -ne 0)
        $manuf = [System.Text.Encoding]::ASCII.GetString($m.ManufacturerName -ne 0)
        
        Write-Host "`n[DEVICE FOUND]" -ForegroundColor Green
        Write-Host "Manufacturer: $manuf"
        Write-Host "Model Name:   $name"
        Write-Host "Serial Num:   $serial"
        Write-Host "Instance ID:  $($m.InstanceName)"
    }
} else {
    Write-Host "No active WMI monitors found. Checking Registry..." -ForegroundColor Yellow
}

# 2. Глубокая проверка реестра на предмет скрытых видео-интерфейсов
Write-Host "`n--- SCANNING REGISTRY FOR HIDDEN SIGNATURES ---" -ForegroundColor Cyan
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Enum\DISPLAY\*\*" | 
    Select-Object DeviceDesc, HardwareID | 
    Format-Table -AutoSize

# 3. Проверка активных видео-портов
Write-Host "`n--- DRIVER STATUS ---" -ForegroundColor Cyan
Get-PnpDevice -Class Monitor | Select-Object Status, FriendlyName, InstanceId | Write-Host

Write-Host "`n--- AUDIT COMPLETE ---" -ForegroundColor Green
