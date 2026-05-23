# 👁‍🗨 STAB IMPERIAL SENTINEL v1.1 [FIXED LOGIC]
$logFile = "c:\Users\StabX\Desktop\Lia\SENTINEL_OVERWATCH.log"

function Write-SentinelLog($message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [SENTINEL]: $message"
    Write-Host $logEntry -ForegroundColor Cyan
    $logEntry | Out-File -FilePath $logFile -Append
}

Write-SentinelLog "--- PROTOCOL ABSOLUTE ZASLON v1.1 ACTIVE ---"
$oldWifi = netsh wlan show networks | Out-String
$oldUsb = Get-PnpDevice -PresentOnly | Select-Object InstanceId

while ($true) {
    # 1. Реальная загрузка ЦП (%)
    $cpuLoad = (Get-WmiObject Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
    if ($cpuLoad -gt 85) {
        Write-SentinelLog "CRITICAL: Real CPU Load is high: $cpuLoad %"
    }

    # 2. Мониторинг Wi-Fi
    $currentWifi = netsh wlan show networks | Out-String
    if ($currentWifi -ne $oldWifi) {
        Write-SentinelLog "ALERT: Wi-Fi Environment Change Detected!"
        $oldWifi = $currentWifi
    }

    # 3. Мониторинг USB
    $currentUsb = Get-PnpDevice -PresentOnly | Select-Object InstanceId
    if ($currentUsb.Count -ne $oldUsb.Count) {
        Write-SentinelLog "EVENT: Hardware Configuration Changed!"
        $oldUsb = $currentUsb
    }

    Start-Sleep -Seconds 5
}
