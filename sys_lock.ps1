# ══════════════════════════════════════════════
# LIA // GHOST_KEY v1.0 — EMERGENCY SHUTDOWN
# ══════════════════════════════════════════════

Write-Host "[!] GHOST_KEY INITIATED..." -ForegroundColor Red

# 1. Clear Clipboard (Protect passwords/data)
Set-Clipboard -Value " "

# 2. Close Browser Windows (Lia Interface)
Get-Process | Where-Object { $_.MainWindowTitle -like "*Lia*" -or $_.ProcessName -eq "chrome" -or $_.ProcessName -eq "msedge" } | Stop-Process -Force -ErrorAction SilentlyContinue

# 3. Stop Bridge Server
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force

# 4. Log the event
$LogPath = "$PSScriptRoot\security_log.txt"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$Timestamp] PANIC BUTTON TRIGGERED. Workspace Secured." | Out-File -FilePath $LogPath -Append

# 5. Lock the Windows Session
rundll32.exe user32.dll,LockWorkStation

Write-Host "[OK] Workspace is now GHOST. System Locked." -ForegroundColor Green
