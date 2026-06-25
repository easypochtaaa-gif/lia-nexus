# STAB OS MAC SPOOF — Run as Administrator
# Right-click → Run with PowerShell (as Admin)

$ErrorActionPreference = "Stop"
Write-Host "===================================="  -ForegroundColor Cyan
Write-Host " STAB OS // MAC SPOOF v1.1"           -ForegroundColor Cyan
Write-Host "===================================="  -ForegroundColor Cyan

# Target: MediaTek Wi-Fi MT7902
$adapter = Get-NetAdapter | Where-Object {
    $_.InterfaceDescription -match "MediaTek" -or $_.Name -match "Беспроводная"
}

if (-not $adapter) {
    Write-Host "[!] WiFi adapter not found!" -ForegroundColor Red
    Read-Host
    exit 1
}

Write-Host "[+] Found: $($adapter.Name) — $($adapter.InterfaceDescription)" -ForegroundColor Green
Write-Host "[+] Current MAC: $($adapter.MacAddress)" -ForegroundColor Yellow

# Generate random locally-administered unicast MAC
$bytes = @(Get-Random -Minimum 0 -Maximum 256)
for ($i = 1; $i -lt 6; $i++) { $bytes += Get-Random -Minimum 0 -Maximum 256 }
$bytes[0] = ($bytes[0] -band 0xFC) -bor 0x02  # locally administered, unicast
$newMac = ($bytes | ForEach-Object { $_.ToString("X2") }) -join ""
$newMacFormatted = ($bytes | ForEach-Object { $_.ToString("X2") }) -join "-"

# Find adapter in registry
$adapterGuid = ($adapter.DeviceID -replace "[{}]", "")
$classPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"

try {
    $found = $false
    Get-ChildItem -Path $classPath -ErrorAction Stop | ForEach-Object {
        $id = (Get-ItemProperty -Path $_.PSPath -Name "NetCfgInstanceId" -ErrorAction SilentlyContinue).NetCfgInstanceId
        if ($id -eq $adapterGuid) {
            Write-Host "[+] Registry key: $($_.PSPath)" -ForegroundColor Green
            Set-ItemProperty -Path $_.PSPath -Name "NetworkAddress" -Value $newMac -Type String -Force
            Write-Host "[+] NetworkAddress set to: $newMac" -ForegroundColor Green
            $found = $true
        }
    }
    if (-not $found) {
        Write-Host "[!] Registry key not found for adapter" -ForegroundColor Red
        Read-Host
        exit 1
    }
} catch {
    Write-Host "[!] Registry access FAILED. Are you running as Administrator?" -ForegroundColor Red
    Write-Host "    Right-click spoof_mac.ps1 → Run with PowerShell"
    Read-Host
    exit 1
}

# Restart adapter
Write-Host "[+] Restarting WiFi adapter..." -ForegroundColor Cyan
Restart-NetAdapter -Name $adapter.Name -Confirm:$false -ErrorAction Stop
Start-Sleep -Seconds 3

# Verify
$newCurrentMac = (Get-NetAdapter -Name $adapter.Name).MacAddress
if ($newCurrentMac -eq $newMacFormatted) {
    Write-Host ""
    Write-Host "===================================="  -ForegroundColor Green
    Write-Host " SUCCESS! MAC changed to: $newMacFormatted" -ForegroundColor Green
    Write-Host " Router sees you as a NEW device now."   -ForegroundColor Green
    Write-Host "===================================="  -ForegroundColor Green
} else {
    Write-Host "[!] MAC change may not have applied. Current: $newCurrentMac" -ForegroundColor Yellow
    Write-Host "    Try rebooting or disabling/re-enabling WiFi manually."    -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host
