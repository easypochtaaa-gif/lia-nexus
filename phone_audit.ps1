# 👁‍🗨 STAB PHONE AUDIT & OPTIMIZATION
# Requites: USB Debugging enabled on Phone

$adb = "c:\Users\StabX\Desktop\Lia\tools\platform-tools\adb.exe"

Write-Host "--- [1] CONNECTING TO NEURAL CORE ---" -ForegroundColor Cyan
& $adb devices

Write-Host "`n--- [2] SECURITY AUDIT: SUSPICIOUS PACKAGES ---" -ForegroundColor Red
# Ищем приложения, которые не являются системными (сторонние)
& $adb shell pm list packages -3 | Out-String | Write-Host

Write-Host "`n--- [3] CHECKING DEVICE ADMINS (Backdoor Check) ---" -ForegroundColor Yellow
& $adb shell dumpsys device_policy | Select-String "admin=" | Write-Host

Write-Host "`n--- [4] PERFORMANCE: MEMORY LOAD ---" -ForegroundColor Green
& $adb shell dumpsys meminfo | Select-String "Total RAM" | Write-Host
& $adb shell top -n 1 -b | select -first 15 | Write-Host

Write-Host "`n--- [5] EXECUTING IMPERIAL OPTIMIZATION ---" -ForegroundColor Cyan
Write-Host ">> Accelerating animations (0.5x)..."
& $adb shell settings put global window_animation_scale 0.5
& $adb shell settings put global transition_animation_scale 0.5
& $adb shell settings put global animator_duration_scale 0.5

Write-Host ">> Purging background cache..."
& $adb shell pm trim-caches 999G

Write-Host ">> Optimizing system apps (dexopt)..."
# Это может занять пару минут, ускоряет запуск приложений
& $adb shell cmd package bg-dexopt-job

Write-Host "`n--- AUDIT COMPLETE. ANALYZE RESULTS ABOVE. ---" -ForegroundColor Green
