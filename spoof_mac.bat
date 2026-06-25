@echo off
REM STAB OS MAC SPOOF — Run as Administrator
echo ====================================
echo  STAB OS // MAC SPOOF v1.0
echo ====================================
echo.

set NEW_MAC=AE2440DF2C62

echo [+] Setting NetworkAddress to %NEW_MAC%...
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}" /v NetworkAddress /d %NEW_MAC% /f /reg:64 2>nul
if %errorlevel% neq 0 (
    echo [!] 64-bit key not found, trying 32-bit...
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}" /v NetworkAddress /d %NEW_MAC% /f 2>nul
)

echo [+] Restarting WiFi adapter...
netsh interface set interface "Беспроводная сеть" admin=disable >nul 2>&1
timeout /t 2 /nobreak >nul
netsh interface set interface "Беспроводная сеть" admin=enable >nul 2>&1

echo.
echo [+] Done! New MAC should be: AE-24-40-DF-2C-62
echo [+] Check: ipconfig /all | find "Physical"
echo.
echo Press any key to exit...
pause >nul
