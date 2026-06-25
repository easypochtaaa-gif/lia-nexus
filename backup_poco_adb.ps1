# LIA // POCO X3 NFC BACKUP via ADB
# Fast, reliable backup using Android Debug Bridge
# Prerequisites: USB debugging enabled, phone authorized

$ErrorActionPreference = "Continue"
$BackupRoot = "D:\POCCO"
$AdbPath = "C:\Users\StabX\AppData\Local\Android\Sdk\platform-tools\adb.exe"
$LogFile = "$BackupRoot\backup_log.txt"

# Create backup folder
New-Item -ItemType Directory -Force $BackupRoot | Out-Null
$startTime = Get-Date

"=== POCO X3 NFC BACKUP (ADB) ===" | Out-File $LogFile
"Start: $startTime" | Out-File $LogFile -Append
"Backup: $BackupRoot" | Out-File $LogFile -Append
"----------------------------------------" | Out-File $LogFile -Append

Write-Host "👁 [POCO BACKUP ADB] Starting full backup to $BackupRoot..." -ForegroundColor Cyan

# Check device
Write-Host "[1/3] Checking device..." -ForegroundColor Yellow
$devices = & $AdbPath devices 2>&1 | Out-String
Write-Host $devices

if ($devices -notmatch 'device\s*$' -and $devices -notmatch 'device\r?\n') {
    if ($devices -match 'unauthorized') {
        Write-Host "❌ Phone NOT authorized! Unlock phone and tap 'Allow USB debugging'." -ForegroundColor Red
        Write-Host "   Then run this script again." -ForegroundColor Red
        exit 1
    }
}

# List common folders on internal storage
Write-Host "[2/3] Scanning phone folders..." -ForegroundColor Yellow
$phoneRoot = "/sdcard"
$folders = & $AdbPath shell ls -1 $phoneRoot 2>&1 | Where-Object { $_ -notmatch '^\.' }

$importantFolders = @(
    "DCIM",       # Photos/Camera
    "Pictures",   # Screenshots, saved images
    "Download",   # Downloads
    "Documents",  # Documents
    "Music",      # Music
    "Movies",     # Videos
    "Ringtones",  # Ringtones
    "Alarms",     # Alarm sounds
    "Notifications", # Notification sounds
    "Podcasts",   # Podcasts
    "Recordings", # Voice recordings
    "Telegram",   # Telegram data (if exists)
    "WhatsApp",   # WhatsApp data (if exists)
    "Viber",      # Viber data
    "Signal",     # Signal data
    "Snapchat",   # Snapchat data
    "TikTok",     # TikTok data
    "Instagram"   # Instagram data
)

$foundFolders = @()
foreach ($f in $folders) {
    $fname = $f.Trim()
    if ($fname -and $fname -ne "") {
        $foundFolders += $fname
    }
}

Write-Host "   Found $($foundFolders.Count) items in phone root" -ForegroundColor Gray

# Pull each folder
Write-Host "[3/3] Copying folders... (this will take a while)" -ForegroundColor Yellow
$totalCopied = 0
$totalFailed = 0

foreach ($folder in $foundFolders) {
    $phonePath = "$phoneRoot/$folder"
    $localPath = Join-Path $BackupRoot $folder

    # Skip Android system folders (protected)
    if ($folder -match '^Android$|^\.|^LOST\.DIR$|^cache$') {
        Write-Host "   SKIP: $folder (system)" -ForegroundColor DarkGray
        "$folder : SKIPPED (system)" | Out-File $LogFile -Append
        continue
    }

    Write-Host "   COPY: $folder → $localPath" -ForegroundColor White
    $result = & $AdbPath pull $phonePath $localPath 2>&1
    $resultStr = ($result | Out-String).Trim()

    if ($LASTEXITCODE -eq 0 -or $resultStr -match 'files pulled') {
        Write-Host "     OK" -ForegroundColor Green
        $totalCopied++
        $resultStr | Out-File $LogFile -Append
    } else {
        Write-Host "     WARN: $resultStr" -ForegroundColor Yellow
        $totalFailed++
        "$folder : FAILED - $resultStr" | Out-File $LogFile -Append
    }
}

# Also backup using Android backup (apps + settings)
Write-Host ""
Write-Host "   Creating Android backup bundle..." -ForegroundColor White
$backupFile = "$BackupRoot\poco_full_backup.ab"
$bkResult = & $AdbPath backup -apk -shared -all -system -f $backupFile 2>&1
Write-Host "   Backup bundle: $backupFile" -ForegroundColor Gray

$endTime = Get-Date
$duration = $endTime - $startTime

# Summary
$summaryText = @"

========================================
POCO X3 NFC BACKUP COMPLETE
========================================
Start:    $startTime
End:      $endTime
Duration: $($duration.ToString('hh\:mm\:ss'))
----------------------------------------
Folders copied:  $totalCopied
Folders failed:  $totalFailed
Destination:     $BackupRoot
========================================
"@

$summaryText | Out-File $LogFile -Append
Write-Host ""
Write-Host "👁 [POCO BACKUP ADB] Done!" -ForegroundColor Cyan
Write-Host $summaryText

# Open folder
explorer $BackupRoot
